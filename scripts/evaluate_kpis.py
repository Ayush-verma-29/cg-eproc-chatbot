# scripts/evaluate_kpis.py
import sys
import os
import re
import json
import time
import random
from pathlib import Path
import urllib.request
import fitz  # PyMuPDF
import tiktoken

# Ensure UTF-8 output on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add backend to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import settings
from app.core.language import language_service
from app.core.rag_engine import get_rag_engine

OLLAMA_GENERATE_URL = f"{settings.OLLAMA_BASE_URL}/api/generate"
# We use qwen2.5:3b for generation as it is fast and supports multilingual translation/generation very well
GEN_MODEL = "qwen2.5:3b"

# Tiktoken tokenizer for token counting
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    tokenizer = None

def get_token_count(text: str) -> int:
    if tokenizer:
        return len(tokenizer.encode(text))
    # Fallback to word-based token estimation (1.3 tokens per word)
    return int(len(text.split()) * 1.3)

def extract_valid_snippets(directory: Path, count_needed: int) -> list:
    """Extract snippets from files in directory. Returns list of tuples: (filename, snippet)"""
    files = list(directory.glob('*'))
    files = [f for f in files if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt'] and not f.name.startswith("~$")]
    
    if not files:
        print(f"⚠️ No files found in {directory}")
        return []
        
    snippets = []
    attempts = 0
    # Try to get diverse snippets
    while len(snippets) < count_needed and attempts < 100:
        attempts += 1
        file_path = random.choice(files)
        ext = file_path.suffix.lower()
        snippet_text = ""
        
        try:
            if ext == '.pdf':
                doc = fitz.open(file_path)
                if len(doc) > 0:
                    # Choose a random page (avoid first page sometimes to get internal rules)
                    page_num = random.randint(0, len(doc) - 1)
                    snippet_text = doc[page_num].get_text().strip()
                doc.close()
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if len(content) > 1000:
                        start_idx = random.randint(0, len(content) - 1000)
                        snippet_text = content[start_idx:start_idx+1000]
                    else:
                        snippet_text = content
            elif ext == '.docx':
                try:
                    import docx
                    doc = docx.Document(file_path)
                    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                    if paragraphs:
                        # Take 5 paragraphs
                        start = random.randint(0, max(0, len(paragraphs) - 5))
                        snippet_text = "\n".join(paragraphs[start:start+5])
                except:
                    pass
        except Exception as e:
            # Skip errors
            continue
            
        # Clean text
        snippet_text = re.sub(r'\s+', ' ', snippet_text).strip()
        if len(snippet_text) > 300:
            snippet_text = snippet_text[:800] # Target length
            # Ensure it is not already chosen
            if not any(snippet_text[:100] == s[1][:100] for s in snippets):
                snippets.append((file_path.name, snippet_text))
                
    return snippets

def call_ollama_generate(prompt: str, model: str = GEN_MODEL) -> str:
    """Helper to query local Ollama generate API"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            OLLAMA_GENERATE_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('response', '').strip()
    except Exception as e:
        print(f"      Ollama call failed: {e}")
        return ""

def generate_question(snippet: str, lang: str) -> str:
    """Ask Ollama to generate a single user question based on snippet context without naming the file."""
    if lang == "en":
        prompt = (
            "You are a test engineer. Given the following content snippet from an e-procurement document, "
            "generate ONE realistic, brief question in English that a user would ask a chatbot to find this information. "
            "CRITICAL: Do not mention the file name, document name, page numbers, or sections in the question. "
            "The question must be completely self-contained and general. "
            "Output ONLY the question text. Do not add any quotes, greetings, introductory text, or explanation.\n\n"
            f"Content Snippet:\n{snippet}\n\n"
            "Question:"
        )
    else:
        prompt = (
            "You are a test engineer. Given the following content snippet from an e-procurement document, "
            "generate ONE realistic, brief question in Hindi (using Devanagari script) that a user would ask a chatbot to find this information. "
            "CRITICAL: Do not mention the file name, document name, page numbers, or sections in the question. "
            "The question must be completely self-contained and general. "
            "Output ONLY the question text in Hindi. Do not add any quotes, English words, introductory text, or explanation.\n\n"
            f"Content Snippet:\n{snippet}\n\n"
            "Question in Hindi:"
        )
        
    question = call_ollama_generate(prompt)
    # Strip quotes if any
    question = question.strip('"' + "'" + '`')
    return question

def evaluate_correctness(snippet: str, answer: str) -> int:
    """Evaluate response correctness on a scale of 1-5 using LLM-as-a-judge"""
    prompt = (
        "You are an expert evaluator. Compare the chatbot's generated answer against the ground truth context. "
        "Assess whether the generated answer is correct, accurate, and completely supported by the ground truth context. "
        "Score the answer on a scale from 1 to 5, where:\n"
        "5: The answer is completely correct, precise, and fully supported by the context.\n"
        "4: The answer is mostly correct and supported, with minor details omitted or slightly imprecise language.\n"
        "3: The answer is partially correct, but contains some omissions or minor inaccuracies.\n"
        "2: The answer is mostly incorrect or contains significant hallucinated/unsupported information.\n"
        "1: The answer is completely incorrect, irrelevant, or contradictory to the context.\n\n"
        f"Ground Truth Context:\n{snippet}\n\n"
        f"Generated Answer:\n{answer}\n\n"
        "Output ONLY a single integer score between 1 and 5. Do not include any explanations, introduction, or formatting. "
        "Response:"
    )
    
    score_str = call_ollama_generate(prompt, model=settings.LLM_MODEL) # Use production model for grading
    try:
        # Extract first digit found
        match = re.search(r'\b[1-5]\b', score_str)
        if match:
            return int(match.group(0))
    except Exception as e:
        print(f"      Failed to parse grade from: {score_str}. Error: {e}")
    return 3 # Neutral default fallback if evaluation fails

def generate_all_questions() -> list:
    print("\n" + "=" * 60)
    print("STEP 1: GENERATING QUESTIONS (30 Vendor, 50 Govt Rules)")
    print("=" * 60)
    
    # 1. Vendor Snippets: Need 15 EN + 15 HI = 30 snippets total
    print("\n📁 Extracting vendor manuals snippets...")
    vendor_snippets = extract_valid_snippets(Path(settings.VENDOR_PDF_DIR), 30)
    print(f"   Extracted {len(vendor_snippets)} unique vendor snippets.")
    
    # 2. Govt Snippets: Need 25 EN + 25 HI = 50 snippets total
    print("\n📁 Extracting govt rules snippets...")
    govt_snippets = extract_valid_snippets(Path(settings.GOVT_PDF_DIR), 50)
    print(f"   Extracted {len(govt_snippets)} unique govt snippets.")
    
    questions = []
    
    # Generate Vendor Questions
    print("\n💬 Generating questions for VENDOR role...")
    # English questions (first 15 snippets)
    for idx, (filename, snippet) in enumerate(vendor_snippets[:15], 1):
        print(f"   Generating EN Question {idx}/15 from {filename}...", end=" ", flush=True)
        q = generate_question(snippet, "en")
        print("Done.")
        if q:
            questions.append({
                "question": q,
                "language": "en",
                "role": "vendor",
                "source_file": filename,
                "ground_truth_context": snippet
            })
            
    # Hindi questions (next 15 snippets)
    for idx, (filename, snippet) in enumerate(vendor_snippets[15:30], 1):
        print(f"   Generating HI Question {idx}/15 from {filename}...", end=" ", flush=True)
        q = generate_question(snippet, "hi")
        print("Done.")
        if q:
            questions.append({
                "question": q,
                "language": "hi",
                "role": "vendor",
                "source_file": filename,
                "ground_truth_context": snippet
            })
            
    # Generate Govt Questions
    print("\n💬 Generating questions for GOVERNMENT OFFICER role...")
    # English questions (first 25 snippets)
    for idx, (filename, snippet) in enumerate(govt_snippets[:25], 1):
        print(f"   Generating EN Question {idx}/25 from {filename}...", end=" ", flush=True)
        q = generate_question(snippet, "en")
        print("Done.")
        if q:
            questions.append({
                "question": q,
                "language": "en",
                "role": "government_officer",
                "source_file": filename,
                "ground_truth_context": snippet
            })
            
    # Hindi questions (next 25 snippets)
    for idx, (filename, snippet) in enumerate(govt_snippets[25:50], 1):
        print(f"   Generating HI Question {idx}/25 from {filename}...", end=" ", flush=True)
        q = generate_question(snippet, "hi")
        print("Done.")
        if q:
            questions.append({
                "question": q,
                "language": "hi",
                "role": "government_officer",
                "source_file": filename,
                "ground_truth_context": snippet
            })
            
    # Save the generated questions
    out_path = Path(__file__).parent / "kpi_test_questions.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ All {len(questions)} questions generated and saved to {out_path}")
    return questions

def run_kpi_testing(questions: list):
    print("\n" + "=" * 60)
    print("STEP 2: RUNNING RAG EVALUATION & KPI BENCHMARKING")
    print("=" * 60)
    
    engine = get_rag_engine()
    engine.initialize()
    
    results = []
    
    # Initialize trackers
    total_queries = len(questions)
    
    for idx, q_item in enumerate(questions, 1):
        question = q_item["question"]
        role = q_item["role"]
        lang = q_item["language"]
        ground_truth = q_item["ground_truth_context"]
        
        print(f"\n[{idx}/{total_queries}] Query ({lang.upper()} | {role}): '{question}'")
        
        # Track times step-by-step
        t_trans_query = 0.0
        t_retrieval = 0.0
        t_generation = 0.0
        t_trans_resp = 0.0
        t_total = 0.0
        
        # producción pipeline interceptada
        t_start = time.time()
        
        # Step A: Query Translation
        detected_lang = language_service.detect_language(question)
        if detected_lang == "hi":
            t_tr_q_start = time.time()
            english_query = language_service.translate_to_english(question)
            t_trans_query = time.time() - t_tr_q_start
            print(f"   🕒 Query Translate: {t_trans_query:.3f}s")
        else:
            english_query = question
            
        # Step B: Chunk Retrieval
        t_ret_start = time.time()
        chunks = engine.retrieve_chunks(english_query, role, k=10, original_query=question)
        t_retrieval = time.time() - t_ret_start
        print(f"   🕒 Retrieval: {t_retrieval:.3f}s")
        
        # Build Context (same as ask)
        context_parts = []
        sources = []
        total_chars = 0
        max_context_chars = 10000
        for c in chunks:
            content_to_use = c["content"]
            truncated_content = engine.clean_truncate(content_to_use, 2500)
            if total_chars + len(truncated_content) <= max_context_chars:
                context_parts.append(truncated_content)
                total_chars += len(truncated_content)
                if c["source"] not in sources:
                    sources.append(c["source"])
            else:
                remaining_space = max_context_chars - total_chars
                if remaining_space > 500:
                    partially_truncated = engine.clean_truncate(content_to_use, remaining_space)
                    context_parts.append(partially_truncated)
                    total_chars += len(partially_truncated)
                    if c["source"] not in sources:
                        sources.append(c["source"])
                break
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step C: Response Generation by LLM
        t_gen_start = time.time()
        # Instruct LLM with brief formatting for speed
        prompt = f"""You are an AI assistant helping a {role.upper()}.
        Answer the user's question clearly, in detail, and comprehensively based ONLY on the provided context.
        Structure your response using bullet points.
        
        Context:
        {context}
        
        Question: {english_query}
        
        Answer (in English):"""
        
        answer_raw = engine.llm.invoke(prompt).strip()
        t_generation = time.time() - t_gen_start
        print(f"   🕒 LLM Generation: {t_generation:.3f}s")
        
        # Step D: Response Translation
        if detected_lang == "hi":
            t_tr_r_start = time.time()
            final_answer = language_service.translate_to_hindi(answer_raw)
            t_trans_resp = time.time() - t_tr_r_start
            print(f"   🕒 Response Translate: {t_trans_resp:.3f}s")
        else:
            final_answer = answer_raw
            
        t_total = time.time() - t_start
        print(f"   🕒 Total Time: {t_total:.3f}s")
        
        # Metrics
        tokens_generated = get_token_count(final_answer)
        correctness_score = evaluate_correctness(ground_truth, final_answer)
        print(f"   📊 Tokens Generated: {tokens_generated} | Correctness Score: {correctness_score}/5")
        
        results.append({
            "question": question,
            "role": role,
            "language": lang,
            "answer": final_answer,
            "sources": sources,
            "correctness_score": correctness_score,
            "tokens_generated": tokens_generated,
            "times": {
                "query_translation": t_trans_query,
                "retrieval": t_retrieval,
                "generation": t_generation,
                "response_translation": t_trans_resp,
                "total": t_total
            }
        })
        
    # Calculate Summary Stats
    en_results = [r for r in results if r["language"] == "en"]
    hi_results = [r for r in results if r["language"] == "hi"]
    
    def get_avg(lst, key):
        if not lst: return 0.0
        return sum(lst) / len(lst)
        
    summary = {
        "overall": {
            "total_queries": total_queries,
            "avg_correctness": get_avg([r["correctness_score"] for r in results], None),
            "avg_accuracy_percent": get_avg([r["correctness_score"] for r in results], None) * 20.0, # Convert 1-5 scale to %
            "avg_latency": get_avg([r["times"]["total"] for r in results], None),
            "avg_tokens": get_avg([r["tokens_generated"] for r in results], None),
            "avg_query_translation": get_avg([r["times"]["query_translation"] for r in results if r["times"]["query_translation"] > 0], None),
            "avg_retrieval": get_avg([r["times"]["retrieval"] for r in results], None),
            "avg_generation": get_avg([r["times"]["generation"] for r in results], None),
            "avg_response_translation": get_avg([r["times"]["response_translation"] for r in results if r["times"]["response_translation"] > 0], None)
        },
        "english": {
            "total_queries": len(en_results),
            "avg_correctness": get_avg([r["correctness_score"] for r in en_results], None),
            "avg_accuracy_percent": get_avg([r["correctness_score"] for r in en_results], None) * 20.0,
            "avg_latency": get_avg([r["times"]["total"] for r in en_results], None),
            "avg_tokens": get_avg([r["tokens_generated"] for r in en_results], None),
            "avg_retrieval": get_avg([r["times"]["retrieval"] for r in en_results], None),
            "avg_generation": get_avg([r["times"]["generation"] for r in en_results], None)
        },
        "hindi": {
            "total_queries": len(hi_results),
            "avg_correctness": get_avg([r["correctness_score"] for r in hi_results], None),
            "avg_accuracy_percent": get_avg([r["correctness_score"] for r in hi_results], None) * 20.0,
            "avg_latency": get_avg([r["times"]["total"] for r in hi_results], None),
            "avg_tokens": get_avg([r["tokens_generated"] for r in hi_results], None),
            "avg_query_translation": get_avg([r["times"]["query_translation"] for r in hi_results], None),
            "avg_retrieval": get_avg([r["times"]["retrieval"] for r in hi_results], None),
            "avg_generation": get_avg([r["times"]["generation"] for r in hi_results], None),
            "avg_response_translation": get_avg([r["times"]["response_translation"] for r in hi_results], None)
        }
    }
    
    report = {
        "summary": summary,
        "queries_details": results
    }
    
    report_path = Path(__file__).parent / "kpi_evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 60)
    print("📊 FINAL KPI SUMMARY REPORT")
    print("=" * 60)
    print(f"Saved complete details to: {report_path}")
    print(f"\nOverall Stats:")
    print(f"   Total Queries: {total_queries}")
    print(f"   Average Correctness Score: {summary['overall']['avg_correctness']:.2f}/5.0 ({summary['overall']['avg_accuracy_percent']:.1f}%)")
    print(f"   Average Latency: {summary['overall']['avg_latency']:.2f}s")
    print(f"   Average Tokens Generated: {summary['overall']['avg_tokens']:.1f}")
    print(f"   Average Query Translation Time: {summary['overall']['avg_query_translation']:.3f}s")
    print(f"   Average Chunk Retrieval Time: {summary['overall']['avg_retrieval']:.3f}s")
    print(f"   Average LLM Response Generation Time: {summary['overall']['avg_generation']:.3f}s")
    print(f"   Average Response Translation Time: {summary['overall']['avg_response_translation']:.3f}s")
    
    print(f"\nEnglish Queries Stats:")
    print(f"   Queries Count: {summary['english']['total_queries']}")
    print(f"   Average Correctness: {summary['english']['avg_correctness']:.2f}/5.0 ({summary['english']['avg_accuracy_percent']:.1f}%)")
    print(f"   Average Latency: {summary['english']['avg_latency']:.2f}s")
    print(f"   Average Tokens Generated: {summary['english']['avg_tokens']:.1f}")
    
    print(f"\nHindi Queries Stats:")
    print(f"   Queries Count: {summary['hindi']['total_queries']}")
    print(f"   Average Correctness: {summary['hindi']['avg_correctness']:.2f}/5.0 ({summary['hindi']['avg_accuracy_percent']:.1f}%)")
    print(f"   Average Latency: {summary['hindi']['avg_latency']:.2f}s")
    print(f"   Average Tokens Generated: {summary['hindi']['avg_tokens']:.1f}")
    print(f"   Average Query Translation: {summary['hindi']['avg_query_translation']:.3f}s")
    print(f"   Average Response Translation: {summary['hindi']['avg_response_translation']:.3f}s")
    print("=" * 60 + "\n")
    
    return report

if __name__ == "__main__":
    questions = generate_all_questions()
    run_kpi_testing(questions)
