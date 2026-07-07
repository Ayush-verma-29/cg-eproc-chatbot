# scripts/test_streaming_pipeline.py
import sys
import re
import time
import queue
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from langchain_community.llms import Ollama
from app.core.config import settings

def get_complete_sentences(buffer: str) -> tuple:
    # Regex to split on sentence ends, ignoring abbreviations and list numbers
    pattern = re.compile(
        r'(?<!\bRs)(?<!\bNo)(?<!\bno)(?<!\bJan)(?<!\bFeb)(?<!\bMar)(?<!\bApr)(?<!\bJun)(?<!\bJul)(?<!\bAug)(?<!\bSep)(?<!\bOct)(?<!\bNov)(?<!\bDec)(?<!\b[A-Za-z])(?<!\b\d)[.!?](?:\s+|\n+)'
    )
    matches = list(pattern.finditer(buffer))
    if not matches:
        return [], buffer
        
    sentences = []
    last_idx = 0
    for match in matches:
        end_idx = match.end()
        sentences.append(buffer[last_idx:end_idx].strip())
        last_idx = end_idx
        
    remaining = buffer[last_idx:]
    return sentences, remaining

def producer_task(llm, prompt, sentence_queue):
    buffer = ""
    try:
        for chunk in llm.stream(prompt):
            buffer += chunk
            sentences, buffer = get_complete_sentences(buffer)
            for s in sentences:
                sentence_queue.put(s)
    except Exception as e:
        print(f"\n[Producer Error] {e}")
        sentence_queue.put(e)
    finally:
        if buffer.strip():
            sentence_queue.put(buffer)
        sentence_queue.put(None)  # Sentinel to stop consumer

def test_pipeline():
    prompt = (
        "<s>[INST] Explain the different modes of procurement on the Chhattisgarh e-Procurement Portal "
        "as described in Chapter 4 in 4 brief points with citations like [Page 132]. [/INST]"
    )
    
    print("1. Initializing GPU Model (mistral:latest)...")
    gpu_llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="mistral:latest",
        temperature=0.0
    )
    
    print("2. Initializing CPU Model (sarvam-cpu)...")
    from app.core.language import language_service
    
    sentence_queue = queue.Queue()
    
    # Start producer thread (GPU generation)
    print("3. Starting Producer Thread (GPU Generation)...")
    t_start = time.time()
    prod_thread = threading.Thread(
        target=producer_task, 
        args=(gpu_llm, prompt, sentence_queue)
    )
    prod_thread.start()
    
    # Consumer loop (CPU translation & print)
    print("4. Starting Consumer Loop (CPU Translation & Streaming)...")
    print("\n--- STREAMING HINDI TRANSLATION ---")
    
    first_token_time = None
    
    while True:
        item = sentence_queue.get()
        if item is None:
            break
        if isinstance(item, Exception):
            print(f"\nError in streaming: {item}")
            break
            
        sentence = item.strip()
        if not sentence:
            continue
            
        # Translate the sentence
        t_trans_start = time.time()
        translated = language_service.translate_to_hindi(sentence)
        t_trans_elapsed = time.time() - t_trans_start
        
        if first_token_time is None:
            first_token_time = time.time() - t_start
            print(f"\n[First Hindi Sentence Time: {first_token_time:.2f}s]\n")
            
        print(f" {translated} (translated in {t_trans_elapsed:.2f}s)")
        
    prod_thread.join()
    total_time = time.time() - t_start
    print("\n-----------------------------------")
    print(f"Total pipeline time: {total_time:.2f} seconds")

if __name__ == "__main__":
    test_pipeline()
