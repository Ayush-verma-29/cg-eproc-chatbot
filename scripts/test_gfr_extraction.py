# test_gfr_extraction.py
import fitz

pdf_path = r"C:\cg-eproc-chatbot\backend\data\govt_rules\FInal_GFR_upto_31_07_2024.pdf"

doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

# Check page 42 specifically
page = doc[41]  # Page 42 is index 41
text = page.get_text()

if "Rule 170" in text:
    print("✅ Rule 170 found on page 42")
    # Print surrounding text
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'Rule 170' in line:
            for j in range(max(0,i-2), min(len(lines), i+5)):
                print(lines[j])
else:
    print("❌ Rule 170 NOT found in extracted text")

doc.close()