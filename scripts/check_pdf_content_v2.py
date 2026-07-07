# scripts/check_pdf_content_v2.py
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

# Unicode/Emoji safe print helpers
def get_safe_symbol(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'ascii')
        return emoji
    except Exception:
        return fallback

SEARCH_SYM = get_safe_symbol("🔍", "[SEARCH]")
NOTE_SYM = get_safe_symbol("📝", "[NOTE]")
FAIL_SYM = get_safe_symbol("❌", "[FAIL]")
DOC_SYM = get_safe_symbol("📄", "[DOC]")

def search_keywords(keywords, description):
    """Search for specific keywords in vector store"""
    vsm = VectorStoreManager()
    govt_store = vsm.get_govt_store()
    
    print(f"\n{'='*60}")
    print(f"{SEARCH_SYM} Searching: {description}")
    print(f"{NOTE_SYM} Keywords: {keywords}")
    print(f"{'='*60}")
    
    try:
        results = govt_store.similarity_search(keywords, k=3)
        
        if not results:
            print(f"{FAIL_SYM} NO RESULTS FOUND")
            return False
        
        for i, doc in enumerate(results):
            print(f"\n{DOC_SYM} Result {i+1}:")
            print(f"   Source: {doc.metadata.get('source', 'Unknown')}")
            # Show first 300 chars of content
            preview = doc.page_content[:300].replace('\n', ' ')
            print(f"   Preview: {preview}...")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("="*60)
    print("  PDF CONTENT DIAGNOSTIC v2 - Using Correct Terminology")
    print("="*60)
    
    # Search with CORRECT GFR terminology
    search_keywords("Rule 170 Bid Security EMD", "GFR Rule 170 (Bid Security)")
    
    search_keywords("Limited Tender Enquiry LTE", "Limited Tender Enquiry (LTE)")
    
    search_keywords("Open Tender Enquiry OTE advertised tender", "Open Tender Enquiry (OTE)")
    
    search_keywords("Micro and Small Enterprises MSE", "MSE (Micro and Small Enterprises)")
    
    search_keywords("GeM Government e-Marketplace", "GeM Portal")
    
    search_keywords("खरीद नियम भण्डार क्रय", "Store Purchase Rules (Hindi)")
    
    print("\n" + "="*60)
    print("📋 VERIFICATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()