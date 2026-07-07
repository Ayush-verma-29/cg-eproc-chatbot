# scripts/check_pdf_content.py
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

FAIL_SYM = get_safe_symbol("❌", "[FAIL]")
DOC_SYM = get_safe_symbol("📄", "[DOC]")

def search_keywords(keywords):
    """Search for specific keywords in vector store"""
    vsm = VectorStoreManager()
    govt_store = vsm.get_govt_store()
    
    print("\n" + "=" * 60)
    print(f"Searching for: {keywords}")
    print("=" * 60)
    
    try:
        results = govt_store.similarity_search(keywords, k=5)
        
        if not results:
            print(f"{FAIL_SYM} NO RESULTS FOUND")
            return False
        
        for i, doc in enumerate(results):
            print(f"\n{DOC_SYM} Result {i+1}:")
            print(f"   Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"   Preview: {doc.page_content[:400]}...")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("PDF CONTENT DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Search for EMD-related content
    search_keywords("EMD earnest money deposit security")
    
    # Search for MSE exemption
    search_keywords("MSE micro small enterprise exemption")
    
    # Search for short tender
    search_keywords("short tender notice limit amount")
    
    # Search for procurement methods
    search_keywords("procurement method open tender limited tender")
    
    # Search for GFR rules about EMD
    search_keywords("Rule 170 EMD")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION:")
    print("=" * 60)
    print("""
If the above searches show NO RESULTS for certain topics:
1. Your PDFs don't contain that information
2. You need to upload additional documents:
   - MSE procurement policy
   - CVC guidelines
   - Chhattisgarh specific procurement rules
   - Short tender guidelines
    """)

if __name__ == "__main__":
    main()