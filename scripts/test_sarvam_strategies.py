# scripts/test_sarvam_strategies.py
import sys
import re
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

# Reconfigure stdout for utf-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def clean_sarvam_hindi(text: str) -> str:
    if not text:
        return text
    
    # 1. Convert Devanagari digits to standard Arabic digits
    devanagari_digits = "०१२३४५६७८९"
    arabic_digits = "0123456789"
    trans_table = str.maketrans(devanagari_digits, arabic_digits)
    text = text.translate(trans_table)
    
    # 2. Fix Marathi leaks
    marathi_replacements = {
        r'\bदेखील\b': 'भी',
        r'\bमर्यादित\b': 'सीमित',
        r'\bवर\b': 'पर',
        r'\bमध्ये\b': 'में',
        r'\bआहे\b': 'है',
        r'\bआहेत\b': 'हैं',
        r'\bकेले\b': 'किया',
        r'\bकेली\b': 'की',
        r'\bहोते\b': 'था',
        r'\bहोती\b': 'थी',
        r'\bनिविधा\b': 'निविदा',
        r'\bनिविध\b': 'निविद',
    }
    for pat, rep in marathi_replacements.items():
        text = re.sub(pat, rep, text)
        
    # 3. Strip end tokens
    text = text.replace("</s>", "").strip()
    return text

def test_strategies():
    english_text = (
        "The provided context does not explicitly mention any rule number for \"short tenders\" or \"limited tendering\". "
        "However, it is mentioned that such tenders can be done without wide publicity in newspapers due to time constraints [Page 317]. "
        "Also, short-term / limited tenders are put on the website of the department as per Office Order No.98/ORD/1 dated 11th Feb., 2004 (applies to limited tenders also) [Clarification section].\n\n"
        "Regarding the process for such tenders, it is stated that they do not require publicity through newspapers and pre-qualified / known vendors are invited during the tender process. "
        "The details of terms can be obtained with the tender form from the concerned office within working days prior to the fixed date [Page 8].\n\n"
        "The contents of the Tender Document for any tendering method, including short or limited tenders, include sections such as Notice Inviting Tender (NIT), Instructions to Bidders (ITB), General Conditions of Contract (GCC), Special Conditions of Contract (SCC) and others [Page 317].\n\n"
        "The tender shall be submitted within the time table fixed in the online tender, and it will be opened as per that schedule. The tenders can be received by registered post or authorized courier [Page 9]."
    )

    llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="mashriram/sarvam-1",
        temperature=0.0,
        num_ctx=4096,
    )

    # Strategy 1: Baseline Prompt (Very Complex)
    print("\n--- STRATEGY 1: Complex Prompt (Baseline) ---")
    terms_str = "DSC, EMD, GFR, GeM, CRN, Rule, Section, Clause, Portal, PAN, GST, IFSC, PWD, L1"
    baseline_prompt = (
        "You are a professional English to Hindi translator. Translate the following English text into clean, natural Devanagari Hindi.\n\n"
        "Constraints:\n"
        "- Output ONLY the final translation. Do NOT add any introduction, notes, explanation, or comments.\n"
        "- Maintain original layout, line breaks, lists, and formatting.\n"
        "- Keep all numbers as standard Arabic numerals (e.g., 1, 2, 3).\n"
        "- Keep page/section references exactly as-is (e.g., [Page 5], [Section 4 Page 25]).\n"
        f"- Keep these specific terms in English: {terms_str}.\n"
        "- NEVER mix English letters with Hindi letters inside a single word.\n"
        "- Use ONLY proper Hindi Devanagari characters.\n\n"
        "Glossary of Preferred Translations:\n"
        "- 'tender' -> 'निविदा' or 'टेंडर' (NEVER use 'प्रस्ताव' or 'बोली' for tender)\n"
        "- 'limited tender' -> 'सीमित निविदा'\n"
        "- 'short tender' / 'short term tender' / 'short-term tender' -> 'अल्पकालीन निविदा' or 'शॉर्ट टेंडर'\n"
        "- 'bid' -> 'बोली' or 'निविदा'\n"
        "- 'bidder' -> 'बोलीदाता'\n"
        "- 'procurement' -> 'प्रोक्योरमेंट' or 'क्रय'\n"
        "- 'corrigendum' -> 'शुद्धिपत्र' or 'संशोधन'\n"
        "- 'GFR' -> 'जीएफआर'\n\n"
        f"Text to translate:\n{english_text}\n\n"
        "Hindi Translation:"
    )
    t0 = time.time()
    res1 = llm.invoke(baseline_prompt).strip()
    print(f"Time: {time.time() - t0:.2f}s")
    print(f"Output:\n{res1}\n")

    # Strategy 2: Simplified Prompt (Few Constraints)
    print("--- STRATEGY 2: Simplified Prompt ---")
    simplified_prompt = (
        "Translate the following English text to clean Devanagari Hindi. Do not add any notes, comments, or explanations. "
        "Keep the numbers and formatting exactly as in the original text.\n\n"
        f"Text to translate:\n{english_text}\n\n"
        "Hindi Translation:"
    )
    t0 = time.time()
    res2 = llm.invoke(simplified_prompt).strip()
    print(f"Time: {time.time() - t0:.2f}s")
    print(f"Raw Output:\n{res2}")
    print(f"Cleaned Output:\n{clean_sarvam_hindi(res2)}\n")

    # Strategy 3: Paragraph Chunking + Simplified Prompt
    print("--- STRATEGY 3: Paragraph Chunking + Simplified Prompt ---")
    paragraphs = [p.strip() for p in english_text.split("\n\n") if p.strip()]
    t0 = time.time()
    translated_paragraphs = []
    for i, p in enumerate(paragraphs):
        chunk_prompt = (
            "Translate the following English paragraph to clean Devanagari Hindi. Do not add any notes or explanations. "
            "Keep the numbers and formatting exactly as in the original.\n\n"
            f"Paragraph to translate:\n{p}\n\n"
            "Hindi Translation:"
        )
        p_trans = llm.invoke(chunk_prompt).strip()
        p_clean = clean_sarvam_hindi(p_trans)
        translated_paragraphs.append(p_clean)
        print(f"Chunk {i+1} Translated.")
    
    full_translation = "\n\n".join(translated_paragraphs)
    print(f"Total Time: {time.time() - t0:.2f}s")
    print(f"Full Chunked Output:\n{full_translation}\n")

if __name__ == "__main__":
    test_strategies()
