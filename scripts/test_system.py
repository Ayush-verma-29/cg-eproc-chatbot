# scripts/test_system.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Unicode/Emoji safe print helpers for Windows consoles
def get_safe_symbol(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'ascii')
        return emoji
    except Exception:
        return fallback

OK_SYM = get_safe_symbol("✅", "[OK]")
FAIL_SYM = get_safe_symbol("❌", "[FAIL]")
WARN_SYM = get_safe_symbol("⚠️", "[WARN]")

def test_ollama():
    import requests
    from app.core.config import settings
    
    print("1. Testing Ollama...", end=" ", flush=True)
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"{OK_SYM} ({len(models)} models loaded)")
            return True
    except:
        print(f"{FAIL_SYM} (Ollama not running)")
        return False

def test_vector_store():
    from app.services.vector_store import VectorStoreManager
    
    print("2. Testing Vector Store...", end=" ", flush=True)
    vsm = VectorStoreManager()
    stats = vsm.get_collection_stats()
    
    vendor_count = stats.get("vendor_documents", 0)
    govt_count = stats.get("govt_documents", 0)
    total_count = vendor_count + govt_count
    
    if total_count > 0:
        print(f"{OK_SYM} ({total_count} chunks: {vendor_count} vendor, {govt_count} govt)")
        return True
    else:
        print(f"{WARN_SYM} (Empty - add documents)")
        return True  # Not a failure, just warning

def test_language_detection():
    from app.core.language import language_service
    
    print("3. Testing Language Detection...", end=" ", flush=True)
    
    tests = [
        ("What is the EMD amount?", "en"),
        ("ईएमडी राशि क्या है?", "hi"),
        ("Bid submission last date?", "en")
    ]
    
    passed = 0
    for text, expected in tests:
        detected = language_service.detect_language(text)
        if detected == expected:
            passed += 1
    
    print(f"{OK_SYM} ({passed}/{len(tests)} passed)")
    return passed == len(tests)

def test_rag_engine():
    from app.core.rag_engine import get_rag_engine
    
    print("4. Testing RAG Engine...", end=" ", flush=True)
    try:
        engine = get_rag_engine()
        status = engine.get_status()
        
        if status["initialized"]:
            print(f"{OK_SYM} (LLM: {status['llm_model']})")
            return True
    except Exception as e:
        print(f"{FAIL_SYM} ({str(e)[:50]})")
        return False

def test_ocr():
    from app.services.ocr_service import ocr_service
    
    print("5. Testing OCR Service...", end=" ", flush=True)
    if ocr_service.reader:
        print(f"{OK_SYM} (EasyOCR ready)")
        return True
    else:
        print(f"{WARN_SYM} (OCR not initialized)")
        return True

def main():
    print("\n" + "=" * 50)
    print("  CG e-Procurement Chatbot - System Test")
    print("=" * 50 + "\n")
    
    results = []
    results.append(("Ollama", test_ollama()))
    results.append(("Vector Store", test_vector_store()))
    results.append(("Language Detection", test_language_detection()))
    results.append(("RAG Engine", test_rag_engine()))
    results.append(("OCR Service", test_ocr()))
    
    print("\n" + "=" * 50)
    print("  Summary")
    print("=" * 50)
    
    for name, passed in results:
        status = f"{OK_SYM} PASS" if passed else f"{FAIL_SYM} FAIL"
        print(f"   {status} | {name}")
    
    print("=" * 50)
    
    # Final recommendation
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 All systems ready! Start the API server:")
        print("   uvicorn backend.app.main:app --reload --port 8001")
    else:
        print("\n⚠️ Some checks failed. Please fix before proceeding.")

if __name__ == "__main__":
    main()