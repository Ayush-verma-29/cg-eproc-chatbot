# scripts/generate_qa_dataset.py
import os
import sys
import json
import random
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Add backend directory to system path to import config and qdrant client
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from qdrant_client import QdrantClient

# Offline fallback message for negative samples
OFFLINE_FALLBACK = (
    "This information is not available in the uploaded documents. "
    "Please refer to the official Chhattisgarh Store Purchase Rules (2002) "
    "or contact your administrative department for clarification."
)

def get_groq_api_key():
    """Retrieve Mistral API key from environment variable."""
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        key = "kD2gfSxmPAPIJ5mvoqdAYX7ebfW6D827"
    return key

def is_chunk_clean(text: str) -> bool:
    """Filter out short or badly garbled OCR text chunks containing Latin-1 garbage or replacement characters."""
    if not text or len(text.strip()) < 80:
        return False
    if '\ufffd' in text:
        return False
    # Check for garbage Western characters typical of broken Devanagari OCR (æ, ø, å, etc.)
    garbage_chars = sum(1 for c in text if '\u0080' <= c <= '\u00ff')
    if garbage_chars / len(text) > 0.01:
        return False
    return True

# -----------------------------------------------------------------------
# Document priority weights for dataset generation.
# Keys are substrings matched against the source filename (case-insensitive).
# Values are relative weights — higher means more samples from that document.
# -----------------------------------------------------------------------
DOCUMENT_WEIGHTS = {
    "store purchase rule cg":    3.50,  # PRIMARY: CG Store Purchase Rules (Hindi)
    "mannual procurement":        2.00,  # CG e-Procurement manual
    "publicpromanual":            2.00,  # Public Procurement Manual
    "corrigendum":                1.50,  # CG e-Procurement instructions
    "manual_offline_tenders":     1.50,  # Offline tender manual
    "chips_bid":                  1.50,  # CHiPS Bid Submission Manual
    "chips_vendor":               1.50,  # CHiPS Vendor Registration Manual
    "emd_challan":                1.50,  # EMD payment manual
    "online_emd":                 1.50,  # EMD refund notice
    "guidelines_to_bidders":      1.50,  # Bidder guidelines
    "compilation_of_cvc":         1.00,  # CVC Tender Guidelines
    "cvc guideline":              1.00,  # CVC circular
    "vigilance manual":           0.80,  # Vigilance Manual (Hindi)
    "final_gfr":                  0.80,  # GFR 2024 English
    "hindi_general_financial":    0.80,  # GFR 2017 Hindi
    "manual_for_procurement":     0.60,  # Works procurement manual
    "gem":                        0.50,  # GeM manuals
    "msme":                       0.50,  # MSME policy
    "it-act":                     0.30,  # IT Act Rules
    "dsc":                        0.30,  # DSC Tutorial
    "faq":                        0.30,  # FAQ docs
    "short tender":               0.40,  # Short tender notices
    "amc":                        0.40,  # AMC/AC short tender
}

def get_doc_weight(source: str) -> float:
    """Return sampling weight for a chunk based on its source filename."""
    src_lower = source.lower()
    for key, weight in DOCUMENT_WEIGHTS.items():
        if key in src_lower:
            return weight
    return 0.50  # Default weight for unrecognised documents

def fetch_all_chunks() -> list:
    """Scroll Qdrant to retrieve all documents and metadata chunks from both vendor and govt databases."""
    print("Reading chunks from local Qdrant Vector Store...")
    all_chunks = []

    # Govt Store
    if os.path.exists(settings.GOVT_DB_DIR):
        print(f"Reading from Government DB directory: {settings.GOVT_DB_DIR}")
        client_govt = QdrantClient(path=str(settings.GOVT_DB_DIR))
        try:
            offset = None
            while True:
                records, offset = client_govt.scroll(
                    collection_name=settings.GOVT_COLLECTION,
                    limit=100,
                    with_payload=True,
                    with_vectors=False,
                    offset=offset
                )
                for r in records:
                    payload = r.payload or {}
                    text = payload.get("page_content", "")
                    if not is_chunk_clean(text):
                        continue
                    meta = payload.get("metadata", {})
                    source = meta.get("source", "") or payload.get("source", "Unknown")
                    all_chunks.append({
                        "text": text,
                        "source": source,
                        "page": meta.get("page", 1),
                        "db": "govt",
                        "weight": get_doc_weight(source)
                    })
                if offset is None:
                    break
        except Exception as e:
            print(f"Govt DB read warning: {e}")
        finally:
            client_govt.close()

    # Vendor Store
    if os.path.exists(settings.VENDOR_DB_DIR):
        print(f"Reading from Vendor DB directory: {settings.VENDOR_DB_DIR}")
        client_vendor = QdrantClient(path=str(settings.VENDOR_DB_DIR))
        try:
            offset = None
            while True:
                records, offset = client_vendor.scroll(
                    collection_name=settings.VENDOR_COLLECTION,
                    limit=100,
                    with_payload=True,
                    with_vectors=False,
                    offset=offset
                )
                for r in records:
                    payload = r.payload or {}
                    text = payload.get("page_content", "")
                    if not is_chunk_clean(text):
                        continue
                    meta = payload.get("metadata", {})
                    source = meta.get("source", "") or payload.get("source", "Unknown")
                    all_chunks.append({
                        "text": text,
                        "source": source,
                        "page": meta.get("page", 1),
                        "db": "vendor",
                        "weight": get_doc_weight(source)
                    })
                if offset is None:
                    break
        except Exception as e:
            print(f"Vendor DB read warning: {e}")
        finally:
            client_vendor.close()

    # Print per-document chunk counts for transparency
    import collections
    doc_counts = collections.Counter(c["source"] for c in all_chunks)
    print(f"\nTotal retrieved chunks: {len(all_chunks)}")
    print("Chunks per source document:")
    for src, cnt in sorted(doc_counts.items(), key=lambda x: -x[1]):
        w = get_doc_weight(src)
        print(f"  [{w:.2f}x] {cnt:4d} chunks  {src}")
    return all_chunks

def call_groq_api(api_key: str, sys_instruction: str, prompt: str) -> dict:
    """Send request to Mistral AI API using OpenAI-compatible chat completions endpoint."""
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": sys_instruction + "\nOutput ONLY raw JSON. Do not wrap in markdown code blocks."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 1024
    }
    
    # Try up to 10 times with backoff for rate limits
    for attempt in range(10):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            if response.status_code == 200:
                res_json = response.json()
                text_out = res_json['choices'][0]['message']['content'].strip()
                if text_out.startswith("```"):
                    if text_out.startswith("```json"):
                        text_out = text_out[7:]
                    else:
                        text_out = text_out[3:]
                    if text_out.endswith("```"):
                        text_out = text_out[:-3]
                    text_out = text_out.strip()
                return json.loads(text_out)
            else:
                if response.status_code == 429:
                    retry_seconds = 60
                    try:
                        import re
                        err_msg = response.json().get("error", {}).get("message", "")
                        m = re.search(r'try again in (?:(\d+)m)?([\d.]+)s', err_msg)
                        if m:
                            mins = int(m.group(1)) if m.group(1) else 0
                            secs = float(m.group(2))
                            retry_seconds = int(mins * 60 + secs) + 2
                    except Exception:
                        pass
                    print(f"   [Rate Limit] Hitting API 429 (attempt {attempt + 1}/10). Sleeping {retry_seconds}s...")
                    time.sleep(retry_seconds)
                else:
                    print(f"   [API Error] HTTP {response.status_code}: {response.text}")
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            if attempt == 9:
                raise e
            time.sleep(2)
    raise Exception("Failed after maximum retries")

def generate_sample(api_key: str, chunk: dict, split_type: str) -> dict:
    """Generate a QA pair instruction based on the linguistic split type."""
    source_name = chunk["source"]
    page_num = chunk["page"]
    text = chunk["text"]
    
    # Setup instructions based on split_type
    if split_type == "en-en":
        sys_instruction = (
            "You are an expert generator of training instruction datasets for the Chhattisgarh e-Procurement Portal.\n"
            "Generate a professional, realistic query in English about e-procurement guidelines based on the text.\n"
            "Generate an accurate answer in English derived strictly from the text.\n"
            "Format the answer as a point-by-point markdown list using short, active sentences.\n"
            "Include citations formatted strictly as [Rule/Section/Clause, Page Y] or [Page Y] at the end of statements where appropriate.\n"
            "Both 'question' and 'answer' must be plain strings. Do not output JSON arrays or nested lists."
        )
        prompt = (
            f"Document Source: {source_name}\nPage: {page_num}\n"
            f"Text content:\n{text}\n\n"
            "Generate a JSON object with 'question' and 'answer' keys as plain strings."
        )
    elif split_type == "hi-hi":
        sys_instruction = (
            "You are an expert generator of training instruction datasets for the Chhattisgarh e-Procurement Portal.\n"
            "Generate a professional, realistic query in pure Hindi (Devanagari script) about e-procurement guidelines based on the text.\n"
            "Generate an accurate answer in pure Hindi (Devanagari script) derived strictly from the text.\n"
            "Format the answer as a point-by-point markdown list.\n"
            "Include Hindi citations formatted strictly as [नियम/धारा, पृष्ठ Y] or [पृष्ठ Y] at the end of statements.\n"
            "Both 'question' and 'answer' must be plain strings. Do not output JSON arrays or nested lists."
        )
        prompt = (
            f"Document Source: {source_name}\nPage: {page_num}\n"
            f"Text content:\n{text}\n\n"
            "Generate a JSON object with 'question' and 'answer' keys as plain strings containing Hindi texts."
        )
    elif split_type == "hinglish-hi":
        sys_instruction = (
            "You are an expert generator of training instruction datasets for the Chhattisgarh e-Procurement Portal.\n"
            "Generate a professional, realistic query in Hinglish (Roman script, mixed English/Hindi as users speak colloquially, e.g. 'EMD rules kya hain?', 'PRC timeline kitna hota hai?') based on the text.\n"
            "Generate an accurate answer in Hindi (Devanagari script) derived strictly from the text.\n"
            "Format the answer as a point-by-point markdown list.\n"
            "Include Hindi citations formatted strictly as [नियम/धारा, पृष्ठ Y] at the end of statements.\n"
            "Both 'question' and 'answer' must be plain strings. Do not output JSON arrays or nested lists."
        )
        prompt = (
            f"Document Source: {source_name}\nPage: {page_num}\n"
            f"Text content:\n{text}\n\n"
            "Generate a JSON object with 'question' (in Hinglish) and 'answer' (in Devanagari Hindi) as plain strings."
        )
    else: # hinglish-hinglish
        sys_instruction = (
            "You are an expert generator of training instruction datasets for the Chhattisgarh e-Procurement Portal.\n"
            "Generate a professional, realistic query in Hinglish (Roman script, mixed English/Hindi, e.g. 'direct purchase limit kya hai?') based on the text.\n"
            "Generate an accurate answer in Hinglish (Roman script, mixed English/Hindi, e.g. 'As per Rule 4.3.1, direct purchase limit ₹50,000 per year hai') derived strictly from the text.\n"
            "Format the answer as a point-by-point markdown list.\n"
            "Include citations formatted strictly as [Rule/Clause, Page Y] at the end of Hinglish statements.\n"
            "Both 'question' and 'answer' must be plain strings. Do not output JSON arrays or nested lists."
        )
        prompt = (
            f"Document Source: {source_name}\nPage: {page_num}\n"
            f"Text content:\n{text}\n\n"
            "Generate a JSON object with 'question' and 'answer' keys in Hinglish (Roman script) as plain strings."
        )
        
    res_data = call_groq_api(api_key, sys_instruction, prompt)
    
    question = res_data.get("question", "")
    answer_raw = res_data.get("answer", "")
    
    if isinstance(question, list):
        question = " ".join(str(q) for q in question)
    else:
        question = str(question).strip()
        
    if isinstance(answer_raw, list):
        answer = "\n".join(f"- {str(item).strip()}" for item in answer_raw if item)
    else:
        answer = str(answer_raw).strip()
        
    return {
        "instruction": question,
        "input": f"Context: {text.strip()}",
        "output": answer
    }

def main():
    parser = argparse.ArgumentParser(description="Synthetic QA Dataset Generator using Groq API")
    parser.add_argument("--test", action="store_true", help="Generate only 5 test samples quickly")
    parser.add_argument("--count", type=int, default=2000, help="Total dataset count (default: 2000)")
    parser.add_argument("--workers", type=int, default=1, help="Number of concurrent workers (default: 1)")
    args = parser.parse_args()
    
    api_key = get_groq_api_key()
    if not api_key:
        print("❌ Error: GROQ_API_KEY environment variable is not set!")
        sys.exit(1)
        
    # Retrieve Qdrant chunks
    all_chunks = fetch_all_chunks()
    if not all_chunks:
        print("❌ Error: No document chunks found in local databases! Ingest documents first.")
        sys.exit(1)
        
    random.seed(42)
    total_count = 5 if args.test else args.count

    # ---------------------------------------------------------------
    # STRATIFIED SAMPLING: Directly control sample count per document
    # group so CG Store Purchase Rules gets the intended 35% share
    # regardless of its smaller raw chunk count (only 67 chunks vs
    # 6670 total). Sampling WITH replacement within each group.
    # ---------------------------------------------------------------

    # Group chunks by source document
    import collections
    chunks_by_source = collections.defaultdict(list)
    for c in all_chunks:
        chunks_by_source[c["source"]].append(c)

    # Define target share (%) per document group. Keys are substrings
    # matched against source filename (case-insensitive, first match wins).
    # Must sum to 100.
    STRATA_TARGETS = [
        ("store purchase rule cg",          35.0),  # PRIMARY document
        ("mannual procurement",              10.0),  # CG e-Proc manual
        ("publicpromanual",                  8.0),   # Public Procurement Manual
        ("corrigendum",                       2.0),  # CG instructions
        ("manual_offline_tenders",            1.0),  # Offline tenders
        ("chips_bid",                         4.0),  # CHiPS Bid Manual
        ("chips_vendor",                      3.0),  # CHiPS Vendor Manual
        ("emd_challan",                       2.0),  # EMD Payment
        ("guidelines_to_bidders",             2.0),  # Bidder guidelines
        ("online_emd",                        1.0),  # EMD Refund
        ("faq_chips",                         1.0),  # FAQ docs
        ("compilation_of_cvc",                3.0),  # CVC Tender guidelines
        ("cvc guideline",                     3.0),  # CVC circular
        ("vigilance manual",                  2.0),  # Vigilance Manual Hindi
        ("final_gfr",                         5.0),  # GFR 2024 English
        ("hindi_general_financial",           5.0),  # GFR 2017 Hindi
        ("manual_for_procurement",            2.0),  # Works procurement
        ("gem",                               2.0),  # GeM manuals
        ("msme",                              1.0),  # MSME policy
        ("short tender",                      1.0),  # Short tender notices
        ("amc",                               1.0),  # AMC/AC short tender
    ]
    # Remaining % goes to unmatched docs
    matched_total = sum(pct for _, pct in STRATA_TARGETS)
    other_pct = max(0.0, 100.0 - matched_total)

    def get_stratum(source: str) -> str:
        src_lower = source.lower()
        for key, _ in STRATA_TARGETS:
            if key in src_lower:
                return key
        return "__other__"

    # Build stratum → chunk pool mapping
    stratum_pools = collections.defaultdict(list)
    for src, chunks in chunks_by_source.items():
        stratum_pools[get_stratum(src)].extend(chunks)

    # Calculate target sample count per stratum
    strata_counts = {}
    for key, pct in STRATA_TARGETS:
        strata_counts[key] = max(1, int(round(total_count * pct / 100.0)))
    strata_counts["__other__"] = max(0, total_count - sum(strata_counts.values()))

    # Redistribute counts from empty pools to the primary stratum
    primary_key = "store purchase rule cg"
    redistributed_count = 0
    for key in list(strata_counts.keys()):
        if not stratum_pools.get(key):
            redistributed_count += strata_counts[key]
            strata_counts[key] = 0

    if redistributed_count > 0:
        strata_counts[primary_key] = strata_counts.get(primary_key, 0) + redistributed_count
        print(f"[Warning] Note: Redistributed {redistributed_count} samples from empty strata pools to primary stratum '{primary_key}'.")

    # Sample with replacement within each stratum
    selected_chunks = []
    print(f"\nGenerating {total_count} synthetic samples...")
    print("Stratified sample distribution:")
    for key, target_n in strata_counts.items():
        if target_n == 0:
            continue
        pool = stratum_pools[key]
        sampled = random.choices(pool, k=target_n)
        selected_chunks.extend(sampled)
        src_label = key if key != "__other__" else "other docs"
        print(f"  {target_n:4d} ({target_n/total_count*100:.1f}%)  [{src_label}]")

    # Trim or pad to exact total_count (re-ensuring total_count matches length)
    random.shuffle(selected_chunks)
    selected_chunks = selected_chunks[:total_count]
    total_count = len(selected_chunks)
    print(f"  ----")
    print(f"  {total_count:4d} total samples selected\n")

    
    # Calculate splits
    # 30% en-en, 30% hi-hi, 20% hinglish-hi, 20% hinglish-hinglish
    splits = []
    en_en_count = int(total_count * 0.3)
    hi_hi_count = int(total_count * 0.3)
    hinglish_hi_count = int(total_count * 0.2)
    hinglish_hinglish_count = total_count - (en_en_count + hi_hi_count + hinglish_hi_count)
    
    splits.extend(["en-en"] * en_en_count)
    splits.extend(["hi-hi"] * hi_hi_count)
    splits.extend(["hinglish-hi"] * hinglish_hi_count)
    splits.extend(["hinglish-hinglish"] * hinglish_hinglish_count)
    random.shuffle(splits)
    
    # Identify 10% of samples as negative adversarial samples
    negative_indices = set(random.sample(range(total_count), int(total_count * 0.1)))
    
    # Threaded worker function
    dataset = []
    
    def process_index(idx):
        chunk = selected_chunks[idx]
        split = splits[idx]
        is_negative = idx in negative_indices
        
        try:
            # Generate positive query first
            sample = generate_sample(api_key, chunk, split)
            if sample:
                time.sleep(1.5) # Throttling delay for Mistral AI API
            if sample and ("\ufffd" in sample["instruction"] or "\ufffd" in sample["output"]):
                print(f"   [Discard] Sample {idx + 1} contains replacement characters, skipping...")
                return None
            
            if is_negative:
                # To make it negative, swap the context input to an unrelated random chunk,
                # and set the output to the offline fallback message
                unrelated_chunk = random.choice(all_chunks)
                while unrelated_chunk["source"] == chunk["source"]:
                    unrelated_chunk = random.choice(all_chunks)
                    
                sample["input"] = f"Context: {unrelated_chunk['text'].strip()}"
                sample["output"] = OFFLINE_FALLBACK
                
            return sample
        except Exception as e:
            print(f"Error generating sample {idx + 1}: {e}")
            return None

    # Run execution concurrently
    max_workers = 1 if args.test else args.workers
    print(f"Starting concurrent generation with {max_workers} worker threads...")
    completed = 0
    
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "qa_dataset.jsonl"
    
    with open(output_file, "w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_index, i): i for i in range(total_count)}
            for future in as_completed(futures):
                idx = futures[future]
                res = future.result()
                if res:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
                    completed += 1
                if completed % 10 == 0 or completed == total_count:
                    print(f"   Progress: {completed}/{total_count} samples completed.")
                    
    print(f"\nGeneration Complete! Saved {completed} samples to: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
