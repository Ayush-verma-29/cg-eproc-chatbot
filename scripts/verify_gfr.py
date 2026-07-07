# scripts/verify_gfr.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import fitz

# Read GFR PDF directly
pdf_path = r"C:\cg-eproc-chatbot\backend\data\govt_rules\FInal_GFR_upto_31_07_2024.pdf"

doc = fitz.open(pdf_path)

print("=" * 60)
print("SEARCHING GFR PDF FOR RULE 170")
print("=" * 60)

found = False
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    
    if "Rule 170" in text or "Bid Security" in text:
        found = True
        print(f"\n✅ Found on Page {page_num + 1}:")
        print("=" * 50)
        # Print lines around the match
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'Rule 170' in line or 'Bid Security' in line:
                start = max(0, i-2)
                end = min(len(lines), i+5)
                for j in range(start, end):
                    print(lines[j])
                print("-" * 50)
                break
        break

if not found:
    print("\n❌ Rule 170 not found in GFR PDF")

doc.close()