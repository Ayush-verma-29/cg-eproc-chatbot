# scripts/test_translation.py
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

# Reconfigure stdout for utf-8
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_translation():
    english_text = (
        "The provided context does not explicitly mention any rule number for \"short tenders\" or \"limited tendering\". "
        "However, it is mentioned that such tenders can be done without wide publicity in newspapers due to time constraints [Page 317]. "
        "Also, short-term / limited tenders are put on the website of the department as per Office Order No.98/ORD/1 dated 11th Feb., 2004 (applies to limited tenders also) [Clarification section].\n\n"
        "Regarding the process for such tenders, it is stated that they do not require publicity through newspapers and pre-qualified / known vendors are invited during the tender process. "
        "The details of terms can be obtained with the tender form from the concerned office within working days prior to the fixed date [Page 8]."
    )
    
    print("Initializing Ollama with llama3.2:3b...")
    llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="llama3.2:3b",
        temperature=0.0,
        num_ctx=4096,
        repeat_penalty=1.3,
    )
    
    terms_str = "DSC, EMD, GFR, GeM, CRN, Rule, Section, Clause, Portal, PAN, GST, IFSC, PWD, L1"
    
    # New proposed prompt
    prompt = (
        "You are a professional English to Hindi translator. Translate the following English text into clean, natural Devanagari Hindi.\n\n"
        "Constraints:\n"
        "- Output ONLY the final translation. Do NOT add any introduction, notes, explanation, or comments.\n"
        "- Maintain original layout, line breaks, lists, and formatting.\n"
        "- Keep all numbers as standard Arabic numerals (e.g., 1, 2, 3).\n"
        "- Keep page/section references exactly as-is (e.g., [Page 5], [Section 4 Page 25]).\n"
        f"- Keep these specific terms in English: {terms_str}.\n\n"
        f"Text to translate:\n{english_text}\n\n"
        "Hindi Translation:"
    )
    
    print("\nEnglish Text to translate:")
    print("-" * 50)
    print(english_text)
    print("-" * 50)
    
    print("\nSending prompt to llama3.2:3b...")
    translation = llm.invoke(prompt).strip()
    
    print("\nTranslated Hindi Output:")
    print("-" * 50)
    print(translation)
    print("-" * 50)

if __name__ == "__main__":
    test_translation()
