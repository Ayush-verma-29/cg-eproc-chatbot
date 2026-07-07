# scripts/debug_vector.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.vector_store import VectorStoreManager
from app.core.config import settings

def debug_search():
    print("=" * 60)
    print("VECTOR STORE DEBUG - Search Test")
    print("=" * 60)
    
    vsm = VectorStoreManager()
    govt_store = vsm.get_govt_store()
    
    # Test queries
    test_queries = [
        "EMD",
        "Bid Security",
        "Rule 170",
        "Earnest Money Deposit",
        "सुरक्षा निधि",
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        print("-" * 40)
        
        try:
            results = govt_store.similarity_search(query, k=5)
            
            if not results:
                print("   ❌ NO RESULTS FOUND")
                continue
            
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "Unknown")
                content_preview = doc.page_content[:200].replace('\n', ' ')
                
                # Check if this is actually GFR
                is_gfr = "GFR" in source or "FInal_GFR" in source
                
                print(f"   {i+1}. Source: {source}")
                print(f"      Is GFR: {'✅ YES' if is_gfr else '❌ NO'}")
                print(f"      Preview: {content_preview}...")
                print()
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_gfr_content():
    """Directly check if GFR PDF contains Rule 170"""
    print("\n" + "=" * 60)
    print("DIRECT PDF CHECK - Looking for Rule 170")
    print("=" * 60)
    
    import fitz
    
    gfr_path = settings.GOVT_PDF_DIR / "FInal_GFR_upto_31_07_2024.pdf"
    
    if not gfr_path.exists():
        print(f"❌ GFR PDF not found at: {gfr_path}")
        return
    
    doc = fitz.open(str(gfr_path))
    found = False
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        if "Rule 170" in text or "Bid Security" in text:
            found = True
            print(f"\n✅ Found on Page {page_num + 1}:")
            print("=" * 40)
            # Print lines around the match
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'Rule 170' in line or 'Bid Security' in line:
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    for j in range(start, end):
                        print(lines[j])
                    print("-" * 40)
                    break
            break
    
    if not found:
        print("❌ Rule 170 NOT found in GFR PDF")
    
    doc.close()

if __name__ == "__main__":
    debug_search()
    check_gfr_content()