# scripts/test_queries.py
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

# Unicode/Emoji safe print helpers
def get_safe_symbol(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'ascii')
        return emoji
    except Exception:
        return fallback

SEARCH_SYM = get_safe_symbol("🔍", "[SEARCH]")
OK_SYM = get_safe_symbol("✅", "[OK]")
FAIL_SYM = get_safe_symbol("❌", "[FAIL]")

def test_search():
    print("=" * 60)
    print("TESTING VECTOR SEARCH")
    print("=" * 60)
    
    vsm = VectorStoreManager()
    govt_store = vsm.get_govt_store()
    
    test_queries = [
        ("EMD", "सुरक्षा निधि"),
        ("short tender", "शॉर्ट टेंडर"),
        ("Rule 170", "नियम 170"),
        ("MSE exemption", "MSE छूट"),
    ]
    
    for eng_query, hin_query in test_queries:
        print(f"\n{SEARCH_SYM} Searching: '{eng_query}'")
        results = govt_store.similarity_search(eng_query, k=3)
        
        if results:
            print(f"   {OK_SYM} Found {len(results)} results")
            for i, doc in enumerate(results):
                source = doc.metadata.get('source', 'Unknown')
                preview = doc.page_content[:150].replace('\n', ' ')
                print(f"      {i+1}. {source}")
                print(f"         {preview}...")
        else:
            print(f"   {FAIL_SYM} No results found")

if __name__ == "__main__":
    test_search()