# scripts/convert_docs_to_pdf.py
import os
import sys
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Ensure paths are correct
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from fpdf import FPDF
from app.core.config import settings

class PDF(FPDF):
    def __init__(self, doc_title):
        super().__init__()
        self.doc_title = doc_title

    def header(self):
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(100, 110, 120)
        self.cell(0, 10, 'Chhattisgarh e-Procurement Portal - Document Library', border=False, align='L')
        self.ln(10)
        self.set_draw_color(220, 225, 230)
        self.line(10, 18, 200, 18)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

def sanitize_text(text):
    """Sanitize text to be fully compatible with standard Latin-1 FPDF fonts."""
    replacements = {
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2013': '-',
        '\u2014': '-',
        '\u2022': '*',  # Bullet point
        '\u2026': '...',
        '\u00a0': ' ',  # Non-breaking space
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def extract_docx_text_paragraphs(path):
    """Extract plain text paragraphs from a .docx file without external packages."""
    try:
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            paragraphs = []
            for p in tree.findall('.//w:p', namespaces):
                texts = []
                for t in p.findall('.//w:t', namespaces):
                    if t.text:
                        texts.append(t.text)
                if texts:
                    paragraphs.append("".join(texts))
                else:
                    # Keep empty lines to preserve spacing if needed, but not too many
                    paragraphs.append("")
            return paragraphs
    except Exception as e:
        print(f"   [ERROR] Error parsing docx {path}: {e}")
        return []

def convert_docx_to_pdf(docx_path, pdf_path):
    print(f"   [INFO] Converting DOCX to PDF...")
    paragraphs = extract_docx_text_paragraphs(docx_path)
    
    title = docx_path.stem.replace('_', ' ').replace('-', ' ')
    pdf = PDF(title)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Document Title header
    pdf.set_font('helvetica', 'B', 15)
    pdf.set_text_color(26, 54, 93) # Dark Blue
    pdf.multi_cell(0, 10, sanitize_text(title.upper()))
    pdf.ln(8)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    
    for p in paragraphs:
        sanitized = sanitize_text(p.strip())
        if not sanitized:
            pdf.ln(4)
            continue
        pdf.multi_cell(0, 6, sanitized)
        pdf.ln(3)
        
    pdf.output(pdf_path)
    print(f"   [SUCCESS] Created: {pdf_path.name}")

def convert_txt_to_pdf(txt_path, pdf_path):
    print(f"   [INFO] Converting TXT to PDF...")
    try:
        with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        title = txt_path.stem.replace('_', ' ').replace('-', ' ')
        pdf = PDF(title)
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Document Title header
        pdf.set_font('helvetica', 'B', 15)
        pdf.set_text_color(26, 54, 93)
        pdf.multi_cell(0, 10, sanitize_text(title.upper()))
        pdf.ln(8)
        
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(50, 50, 50)
        
        for line in lines:
            sanitized = sanitize_text(line.strip())
            if not sanitized:
                pdf.ln(4)
                continue
            pdf.multi_cell(0, 6, sanitized)
            pdf.ln(2)
            
        pdf.output(pdf_path)
        print(f"   [SUCCESS] Created: {pdf_path.name}")
    except Exception as e:
        print(f"   [ERROR] Error converting TXT: {e}")

def main():
    print("=" * 70)
    print("  Document Library Pre-Conversion: .docx and .txt to .pdf")
    print("=" * 70)
    
    backup_dir = ROOT_DIR / "backend" / "data" / "backup_original_non_pdfs"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths to search
    dirs_to_check = [
        (settings.VENDOR_PDF_DIR, "vendor"),
        (settings.GOVT_PDF_DIR, "govt")
    ]
    
    converted_count = 0
    
    for folder, category in dirs_to_check:
        folder_path = Path(folder)
        if not folder_path.exists():
            continue
            
        print(f"\n[INFO] Checking {category} directory: {folder_path.name}")
        
        # Find docx and txt files
        files_to_convert_set = set()
        for ext in ['*.docx', '*.DOCX', '*.txt', '*.TXT']:
            for f in folder_path.glob(ext):
                files_to_convert_set.add(f)
        files_to_convert = sorted(list(files_to_convert_set))
        
        for file_path in files_to_convert:
            if file_path.name.startswith("~$"): # Skip lock files
                continue
                
            print(f"[INFO] Found: {file_path.name}")
            pdf_path = file_path.with_suffix('.pdf')
            
            # Convert
            if file_path.suffix.lower() == '.docx':
                convert_docx_to_pdf(file_path, pdf_path)
            elif file_path.suffix.lower() == '.txt':
                convert_txt_to_pdf(file_path, pdf_path)
                
            # Move original to backup
            dest_backup = backup_dir / file_path.name
            shutil.move(str(file_path), str(dest_backup))
            print(f"   [SUCCESS] Original moved to backup: backup_original_non_pdfs/{file_path.name}")
            converted_count += 1
            
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Pre-conversion completed: Converted {converted_count} files.")
    print("=" * 70)
    
    if converted_count > 0:
        # Re-run ingestion to clean up DB
        print("\n[INFO] Re-ingesting document collections with new PDFs...")
        import subprocess
        # Execute ingest_documents.py with force parameter or direct call
        sys.path.insert(0, str(ROOT_DIR / "scripts"))
        import ingest_documents
        # Run DB reset automatically
        ingest_documents.delete_all_data(force=True)
        ingest_documents.main()
        print("\n[SUCCESS] Ingestion complete. Chatbot now references clean PDF documents!")
    else:
        print("\n[INFO] No non-PDF files found to convert.")

if __name__ == '__main__':
    main()
