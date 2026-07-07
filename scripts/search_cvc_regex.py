# scripts/search_cvc_regex.py
import sys
import re
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
    
    # We want to fetch all chunks and print ones containing dates or circular patterns
    print("Fetching documents...")
    collection = govt_store._collection
    results = collection.get(include=["documents", "metadatas"])
    
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    
    print(f"Total documents: {len(documents)}")
    
    # Regex to find something that looks like 03.02.2044 or similar
    pattern = re.compile(r'03\.02\.\d{4}|2044|08,\d{3},\d{4}')
    matches = 0
    for doc, meta in zip(documents, metadatas):
        if pattern.search(doc):
            matches += 1
            print(f"\n--- Match {matches} (Source: {meta.get('source')}) ---")
            print(doc[:800])
            if matches >= 10:
                break

if __name__ == "__main__":
    search()
