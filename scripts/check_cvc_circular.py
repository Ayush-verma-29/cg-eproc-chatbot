# scripts/check_cvc_circular.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.vector_store import VectorStoreManager

def search():
    vsm = VectorStoreManager()
    govt_store = vsm.get_govt_store()
    
    # Let's search for "2044" or "08," or "03.02"
    query = "03.02.2044"
    print(f"Searching for: '{query}'")
    results = govt_store.similarity_search(query, k=5)
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} (Source: {doc.metadata.get('source')}) ---")
        print(doc.page_content[:600])

if __name__ == "__main__":
    search()
