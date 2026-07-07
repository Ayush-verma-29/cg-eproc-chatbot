# scripts/verify_dual_hardware.py
import sys
import time
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test():
    print("1. Calling mistral:latest (GPU model)...")
    mistral_llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="mistral:latest",
        temperature=0.0
    )
    # Simple call to activate Mistral in memory
    t0 = time.time()
    res1 = mistral_llm.invoke("Hi. Respond with 'Hello'.").strip()
    print(f"   Mistral response: '{res1}' (took {time.time() - t0:.2f}s)")
    
    print("\n2. Calling sarvam-cpu:latest (CPU model)...")
    sarvam_llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="sarvam-cpu",
        temperature=0.0
    )
    # Simple call to activate Sarvam-cpu in memory
    t0 = time.time()
    res2 = sarvam_llm.invoke("Translate this: Hello").strip()
    print(f"   Sarvam response: '{res2}' (took {time.time() - t0:.2f}s)")
    
    print("\n3. Querying active models hardware status...")
    try:
        output = subprocess.check_output("ollama ps", shell=True, text=True)
        print("\n--- OLLAMA STATUS ---")
        print(output)
        print("---------------------")
    except Exception as e:
        print("Error checking status:", e)

if __name__ == "__main__":
    test()
