# scripts/test_sarvam_cleanup.py
import sys
import re
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

def clean_translation(text: str) -> str:
    if not text:
        return text
    
    # 1. Convert Devanagari digits to Arabic digits
    devanagari_digits = "०१२३४५६७८९"
    arabic_digits = "0123456789"
    trans_table = str.maketrans(devanagari_digits, arabic_digits)
    text = text.translate(trans_table)
    
    # 2. Fix Marathi leaks (e.g., "देखील" -> "भी")
    text = re.sub(r'\bदेखील\b', 'भी', text)
    
    # 3. Clean trailing tokens
    text = text.replace("</s>", "").strip()
    
    return text

def test_sarvam():
    print("Testing mashriram/sarvam-1 with cleanup...")
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
    
    terms_str = "DSC, EMD, GFR, GeM, CRN, Rule, Section, Clause, Portal, PAN, GST, IFSC, PWD, L1"
    
    prompt = (
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
    
    start_time = time.time()
    res = llm.invoke(prompt).strip()
    elapsed = time.time() - start_time
    
    cleaned = clean_translation(res)
    print(f"Time taken: {elapsed:.2f} seconds")
    with open("scripts/sarvam_output.txt", "w", encoding="utf-8") as out_f:
        out_f.write(cleaned)
    print("Cleaned translation written to scripts/sarvam_output.txt")

if __name__ == "__main__":
    test_sarvam()
