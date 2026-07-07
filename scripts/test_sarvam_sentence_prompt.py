# scripts/test_sarvam_sentence_prompt.py
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

def test_prompt():
    sentence = "However, it is mentioned that such tenders can be done without wide publicity in newspapers due to time constraints [Page 317]."
    
    llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="mashriram/sarvam-1",
        temperature=0.0,
        num_ctx=4096,
    )
    
    prompts = [
        # Prompt 1: Simple
        "Translate this English sentence to Hindi: \"" + sentence + "\"\nHindi:",
        
        # Prompt 2: Simple instruction to keep page references
        "Translate this English sentence to Hindi. Do not change or remove bracketed text like [Page 317].\n\nEnglish: " + sentence + "\nHindi:",
        
        # Prompt 3: Minimalist instruction
        "Translate the following sentence to Hindi. Keep [Page 317] as is.\n\nEnglish: " + sentence + "\nHindi:"
    ]
    
    for i, p in enumerate(prompts):
        print(f"\n--- PROMPT {i+1} ---")
        t0 = time.time()
        res = llm.invoke(p).strip()
        print(f"Time: {time.time() - t0:.2f}s")
        print(f"Output: {res}")

if __name__ == "__main__":
    test_prompt()
