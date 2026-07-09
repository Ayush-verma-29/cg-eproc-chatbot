# backend/app/services/document_processor.py
import os
from pathlib import Path
from typing import List, Dict, Tuple
import re
import io
import fitz  # PyMuPDF
from PIL import Image

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.core.config import settings
from app.services.ocr_service import ocr_service
from app.core.language import language_service
import pytesseract

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "। ", ". ", " ", ""],
            length_function=len,
        )
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text without destroying layout newlines"""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'([\u0900-\u097F])\s+([\u0900-\u097F])', r'\1\2', text)
        text = re.sub(r'[^\w\s\.\,\-\/\₹\(\)\%\u0900-\u097F\n]', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def clean_layout_newlines(self, text: str) -> str:
        """Join lines from multi-column PDF layouts by merging adjacent lines that do not end in sentence punctuation or start with bullets/rules."""
        if not text:
            return ""
        lines = text.split('\n')
        cleaned_lines = []
        
        # Regex for list/bullet markers (including Devanagari numerals and list items)
        # e.g., "(i)", "1.", "-", "a.", "(क)", "(1)"
        bullet_pattern = re.compile(r'^\s*(?:\([a-z0-9\u0900-\u097f]+\)|\d+\.|\-|[a-z]\.)\s*', re.I)
        
        current_line = ""
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_line:
                    cleaned_lines.append(current_line)
                    current_line = ""
                cleaned_lines.append("")
                continue
                
            if not current_line:
                current_line = stripped
                continue
                
            is_bullet = bullet_pattern.match(stripped)
            is_rule_start = (
                stripped.startswith("Rule ") or 
                stripped.startswith("Rule-") or 
                stripped.startswith("Rule\t") or
                stripped.startswith("नियम ") or 
                stripped.startswith("नियम-")
            )
            
            # Check if current line ends with sentence-ending punctuation
            ends_with_punc = current_line[-1] in ['.', '!', '?', '।', ':']
            
            if is_bullet or is_rule_start or ends_with_punc:
                cleaned_lines.append(current_line)
                current_line = stripped
            else:
                # Merge lines with a space
                current_line += " " + stripped
                
        if current_line:
            cleaned_lines.append(current_line)
            
        return "\n".join([l for l in cleaned_lines if l.strip()])

    def filter_header_footer_lines(self, text: str, filename: str) -> str:
        """Strip generic page numbers and empty lines from documents to reduce layout noise"""
        lines = text.split('\n')
        
        # Identify indices of non-empty lines to locate headers/footers
        non_empty_indices = [i for i, line in enumerate(lines) if line.strip()]
        if not non_empty_indices:
            return text
            
        # Consider the first 3 and last 3 non-empty lines as potential header/footer zones
        header_indices = set(non_empty_indices[:3])
        footer_indices = set(non_empty_indices[-3:])
        header_footer_indices = header_indices.union(footer_indices)
        
        cleaned_lines = []
        
        # Generic noise patterns (applies to all documents)
        noise_patterns = [
            # Pure numbers (standard page numbers)
            re.compile(r'^\s*\d+\s*$', re.I),
            # "Page X of Y" or "Page X"
            re.compile(r'^\s*Page\s+\d+(?:\s+of\s+\d+)?\s*$', re.I),
        ]
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            
            is_noise = False
            # Only apply generic page number noise patterns in the header/footer zones
            if i in header_footer_indices:
                for pattern in noise_patterns:
                    if pattern.match(stripped):
                        is_noise = True
                        break
            
            if not is_noise:
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines)

    def infer_topics_from_filename(self, filename: str) -> List[str]:
        """Extract topics from filename based on keywords"""
        try:
            from app.core.rag_engine import TOPIC_KEYWORDS
        except ImportError:
            # Fallback local definition
            TOPIC_KEYWORDS = {
                "emd": ["emd", "earnest money", "bid security", "security deposit"],
                "gfr": ["gfr", "general financial rules", "general financial rule", "rule", "rules"],
                "gem": ["gem", "government e-marketplace", "gem portal"],
                "cvc": ["cvc", "vigilance", "anti corruption"],
                "registration": ["register", "registration", "vendor registration", "supplier registration"],
                "dsc": ["dsc", "digital signature"],
                "bid_submission": ["bid submission", "submission", "submit bid", "tender submission"],
                "short_tender": ["short tender", "short term tender"],
                "service_procurement": ["service procurement", "consulting services"],
                "msme": ["msme", "mse", "micro and small"],
                "faq": ["faq", "frequently asked questions"],
            }
        
        normalized = filename.lower()
        topics = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                topics.append(topic)
        return topics
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, bool]:
        """Extract text from PDF using PyMuPDF with OCR fallback"""
        text = ""
        force_ocr_for_doc = False
        try:
            doc = fitz.open(pdf_path)
            
            # Check if this PDF uses Kruti Dev / legacy font encoding
            for page_num in range(min(3, len(doc))):
                page_text = doc[page_num].get_text()
                # Check for common Kruti Dev signatures: 'kklu (शासन), fu;e (नियम), foHkkx (विभाग), fufonk (निविदा), Hk.Mkj (भंडार)
                if page_text and any(sig in page_text for sig in ["'kklu", "fu;e", "foHkkx", "fufonk", "Hk.Mkj"]):
                    force_ocr_for_doc = True
                    break
            
            if force_ocr_for_doc:
                print(f"   [Warning] Detected Kruti Dev/legacy Hindi font in {Path(pdf_path).name}. Forcing OCR to extract Unicode text...")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text() if not force_ocr_for_doc else ""
                
                if page_text and page_text.strip():
                    filtered_page_text = self.filter_header_footer_lines(page_text, Path(pdf_path).name)
                    cleaned_page_text = self.clean_layout_newlines(filtered_page_text)
                    if cleaned_page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += cleaned_page_text + "\n"
                else:
                    # Use OCR for scanned pages
                    if os.environ.get("SKIP_OCR") == "1":
                        continue
                    ocr_reason = "has no text" if not force_ocr_for_doc else "forced due to legacy font"
                    print(f"   Page {page_num + 1} using OCR ({ocr_reason})...")
                    try:
                        pix = page.get_pixmap(dpi=150)
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Primary OCR: Tesseract (blazing fast on CPU)
                        page_text = pytesseract.image_to_string(img, lang='hin+eng')
                        if page_text and page_text.strip():
                            filtered_page_text = self.filter_header_footer_lines(page_text, Path(pdf_path).name)
                            cleaned_page_text = self.clean_layout_newlines(filtered_page_text)
                            if cleaned_page_text.strip():
                                text += f"\n--- Page {page_num + 1} (OCR-Tesseract) ---\n"
                                text += cleaned_page_text + "\n"
                        elif ocr_service.reader:
                            # Secondary OCR: EasyOCR (slower backup on CPU)
                            page_text = ocr_service.extract_text_from_pdf_page(img)
                            if page_text:
                                filtered_page_text = self.filter_header_footer_lines(page_text, Path(pdf_path).name)
                                cleaned_page_text = self.clean_layout_newlines(filtered_page_text)
                                if cleaned_page_text.strip():
                                    text += f"\n--- Page {page_num + 1} (OCR-EasyOCR) ---\n"
                                    text += cleaned_page_text + "\n"
                    except Exception as e:
                        print(f"   OCR error on page {page_num + 1}: {e}")
            doc.close()
        except Exception as e:
            print(f"Error extracting text: {e}")
        
        return self.clean_text(text), force_ocr_for_doc
    
    def extract_text_from_docx(self, docx_path: str) -> Tuple[str, bool]:
        """Extract text from DOCX file using built-in zipfile and xml parser"""
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(docx_path) as z:
                xml_content = z.read('word/document.xml')
                root = ET.fromstring(xml_content)
                texts = []
                for elem in root.iter():
                    if elem.tag.endswith('t'): # Match w:t elements
                        if elem.text:
                            texts.append(elem.text)
                combined_text = " ".join(texts)
                return self.clean_text(combined_text), False
        except Exception as e:
            print(f"Error reading DOCX {docx_path}: {e}")
            return "", False

    def extract_text_from_txt(self, txt_path: str) -> Tuple[str, bool]:
        """Extract text from TXT file"""
        try:
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                return self.clean_text(f.read()), False
        except Exception as e:
            print(f"Error reading TXT {txt_path}: {e}")
            return "", False

    def process_directory(self, directory: Path, role: str) -> List[Document]:
        """Process all PDFs, DOCXs, and TXTs in a directory with role assignment (NO DUPLICATES)"""
        all_chunks = []
        
        # Glob for pdf, docx, txt files (case-insensitive)
        files = set()
        for ext in ['*.pdf', '*.PDF', '*.docx', '*.DOCX', '*.txt', '*.TXT']:
            for f in directory.glob(ext):
                # Ignore temporary office lock files starting with ~$
                if not f.name.startswith("~$"):
                    files.add(f)  # Set automatically removes duplicates
        
        files = sorted(list(files))  # Convert back to sorted list
        
        if not files:
            print(f"   [Warning] No matching files found in {directory}")
            return []
        
        print(f"   [Files] Found {len(files)} file(s) in {directory.name}")
        
        for file_path in files:
            print(f"\n   [Processing] ({role}): {file_path.name}")
            
            ext = file_path.suffix.lower()
            if ext == '.pdf':
                text, force_ocr_for_doc = self.extract_text_from_pdf(str(file_path))
            elif ext == '.docx':
                text, force_ocr_for_doc = self.extract_text_from_docx(str(file_path))
            elif ext == '.txt':
                text, force_ocr_for_doc = self.extract_text_from_txt(str(file_path))
            else:
                text, force_ocr_for_doc = "", False
            
            if not text.strip():
                print(f"   [Warning] No text extracted from {file_path.name}")
                continue
            
            # Create document with role metadata
            doc = Document(
                page_content=text,
                metadata={
                    "source": file_path.name,
                    "file_path": str(file_path),
                    "role": role,
                    "file_size": file_path.stat().st_size,
                    "processed_date": str(file_path.stat().st_mtime)
                }
            )
            
            chunks = self.text_splitter.split_documents([doc])
            
            # Determine if Hindi document based on filename, forced OCR, or character density
            is_hindi_doc = False
            if "hindi" in file_path.name.lower():
                is_hindi_doc = True
            elif force_ocr_for_doc:
                is_hindi_doc = True
            elif language_service.is_hindi_document(text):
                is_hindi_doc = True
                
            if is_hindi_doc:
                print(f"   [Hindi Document] Document detected as Hindi. Translating {len(chunks)} chunks to English for vector indexing...")
                
                # Extract chunk texts
                chunk_texts = [chunk.page_content for chunk in chunks]
                # Pre-populate original Hindi text in metadata
                for chunk in chunks:
                    chunk.metadata["original_hindi"] = chunk.page_content
                
                # Batch translate chunk texts
                translated_contents = language_service.translate_chunks_to_english(chunk_texts)
                
                # Assign back
                for chunk, trans_content in zip(chunks, translated_contents):
                    chunk.page_content = trans_content
            
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = f"{role}_{file_path.stem}_chunk_{i:04d}"
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(chunks)
                chunk.metadata["role"] = role
                chunk.metadata["topics"] = ",".join(self.infer_topics_from_filename(file_path.name))
                if is_hindi_doc:
                    chunk.metadata["language"] = "hi"
            
            all_chunks.extend(chunks)
            print(f"   [Success] Created {len(chunks)} chunks (Total chars: {len(text):,})")
        
        print(f"   [Total] TOTAL for {role}: {len(all_chunks)} chunks from {len(files)} files")
        return all_chunks

if __name__ == "__main__":
    processor = DocumentProcessor()
    
    vendor_chunks = processor.process_directory(settings.VENDOR_PDF_DIR, "vendor")
    govt_chunks = processor.process_directory(settings.GOVT_PDF_DIR, "government_officer")
    
    print(f"\n✅ Vendor chunks: {len(vendor_chunks)}")
    print(f"✅ Government chunks: {len(govt_chunks)}")