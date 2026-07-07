# scripts/test_sarvam_list_translation.py
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from langchain_community.llms import Ollama
from app.core.config import settings
from app.core.language import language_service

def test():
    test_sentences = [
        "1. **Direct Purchase**: This method is applicable when the purchase amount is less than Rs. 50,000.",
        "2. **L1 Purchase**: Applicable for purchases above Rs. 50,000.",
        "3. **Purchasing through GeM Portal**: This is suitable under various situations including emergency circumstances like COVID-19."
    ]
    
    llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="sarvam-cpu",
        temperature=0.0
    )
    
    print("Testing translation of list items with numbers:")
    for s in test_sentences:
        prompt = f"Translate this English text to Hindi: \"{s}\"\nHindi:"
        res = llm.invoke(prompt).strip()
        print(f"\nOriginal: {s}")
        print(f"Raw Output: {repr(res)}")
        cleaned = language_service.clean_sarvam_hindi_output(res)
        cleaned = language_service.clean_translated_hindi(cleaned)
        print(f"Cleaned Output: {repr(cleaned)}")

if __name__ == "__main__":
    test()
