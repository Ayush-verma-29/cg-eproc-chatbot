# scripts/check_pdf_extraction.py
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.document_processor import DocumentProcessor

dp = DocumentProcessor()

files_to_check = [
    Path("backend/data/govt_rules/11.02.2004 transp in short term tender.pdf"),
    Path("backend/data/govt_rules/2. Notification_EMDExemption.pdf")
]

for fp in files_to_check:
    print(f"\nChecking: {fp.name}")
    if not fp.exists():
        print("❌ File does not exist!")
        continue
    text, force_ocr = dp.extract_text_from_pdf(str(fp))
    print(f"Force OCR: {force_ocr}")
    print(f"Extracted Length: {len(text)} characters")
    if text:
        print(f"Snippet: {text[:500]}")
    else:
        print("❌ Text is empty!")
