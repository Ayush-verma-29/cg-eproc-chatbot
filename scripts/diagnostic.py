# scripts/diagnostic.py
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
from app.core.config import settings

# Unicode/Emoji safe print helpers for Windows consoles
def get_safe_symbol(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'ascii')
        return emoji
    except Exception:
        return fallback

OK_SYM = get_safe_symbol("✅", "[OK]")
FAIL_SYM = get_safe_symbol("❌", "[FAIL]")
INFO_SYM = get_safe_symbol("📊", "[STATS]")
SEARCH_SYM = get_safe_symbol("🔍", "[SEARCH]")
DOC_SYM = get_safe_symbol("📄", "[DOC]")

def run_diagnostic():
    print("=" * 70)
    print("  VECTOR STORE DIAGNOSTIC TOOL")
    print("=" * 70)
    
    vsm = VectorStoreManager()
    govt_store = vsm.get_govt_store()
    
    # Test 1: Check if store has data
    print(f"\n{INFO_SYM} TEST 1: Vector Store Status")
    print("-" * 40)
    try:
        count = govt_store._collection.count()
        print(f"   {OK_SYM} Government documents in store: {count} chunks")
        if count == 0:
            print(f"   {FAIL_SYM} STORE IS EMPTY! Run ingestion first.")
            return
    except Exception as e:
        print(f"   {FAIL_SYM} Error: {e}")
        return
    
    # Test 2: Search for EMD related content
    print(f"\n{SEARCH_SYM} TEST 2: Searching for 'EMD'")
    print("-" * 40)
    
    search_terms = [
        "EMD",
        "Earnest Money Deposit", 
        "Bid Security",
        "सुरक्षा निधि",
        "Rule 170",
        "security deposit percentage"
    ]
    
    for term in search_terms:
        print(f"\n   Searching: '{term}'")
        results = govt_store.similarity_search(term, k=3)
        
        if results:
            print(f"   {OK_SYM} Found {len(results)} results")
            for i, doc in enumerate(results):
                source = doc.metadata.get('source', 'Unknown')
                # Show first 200 chars
                preview = doc.page_content[:200].replace('\n', ' ')
                print(f"      {i+1}. {source}")
                print(f"         {preview}...")
        else:
            print(f"   {FAIL_SYM} No results found")
    
    # Test 3: Direct search in GFR PDF
    print(f"\n{DOC_SYM} TEST 3: Checking GFR PDF directly")
    print("-" * 40)
    
    # Search specifically for GFR content
    gfr_search = "GFR Rule 170"
    results = govt_store.similarity_search(gfr_search, k=5)
    
    if results:
        for doc in results:
            source = doc.metadata.get('source', 'Unknown')
            if 'GFR' in source or 'Final' in source:
                print(f"   {OK_SYM} Found in: {source}")
                preview = doc.page_content[:300].replace('\n', ' ')
                print(f"      Content: {preview}...")
                break
    else:
        print(f"   {FAIL_SYM} No GFR content found in vector store")
    
    print("\n" + "=" * 70)
    print(f"{OK_SYM} Diagnostic complete")
    print("=" * 70)

if __name__ == "__main__":
    run_diagnostic()