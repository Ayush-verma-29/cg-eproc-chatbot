# scripts/inspect_short_tender_pdfs.py
import sys
from pathlib import Path
import fitz

# Set stdout encoding
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def inspect_pdf(pdf_path):
    print(f"\n==================================================")
    print(f"INSPECTING: {pdf_path.name}")
    print(f"==================================================")
    
    try:
        doc = fitz.open(str(pdf_path))
        print(f"Total pages: {len(doc)}")
        
        # Read first few pages or search for keywords
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            print(f"\n--- Page {page_num + 1} ---")
            # Print first 800 chars
            print(text[:1500])
            if len(text) > 1500:
                print("... [TRUNCATED] ...")
        
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")

def main():
    govt_dir = Path("backend/data/govt_rules")
    pdf_files = [
        govt_dir / "short tender notice 2 days.pdf",
        govt_dir / "11.02.2004 transp in short term tender.pdf",
        govt_dir / "160616_AMC_AC short tender.pdf"
    ]
    
    for pdf in pdf_files:
        if pdf.exists():
            inspect_pdf(pdf)
        else:
            print(f"PDF not found: {pdf}")

if __name__ == "__main__":
    main()
