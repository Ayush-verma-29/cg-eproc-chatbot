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

KRUTI_DEV_SIGNATURES = ("'kklu", "fu;e", "foHkkx", "fufonk", "Hk.Mkj")
LEGACY_TEMP_PDF_NAMES = frozenset({"temp_visual_ocr.pdf"})


class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "। ", ". ", " ", ""],
            length_function=len,
        )

    @staticmethod
    def _is_ingestion_skip_file(file_path: Path) -> bool:
        """Skip temp OCR artifacts and Office lock files during directory ingestion."""
        name_lower = file_path.name.lower()
        if file_path.name.startswith("~$"):
            return True
        if name_lower in LEGACY_TEMP_PDF_NAMES:
            return True
        if name_lower.startswith(".temp_ocr_"):
            return True
        return False

    @staticmethod
    def _detect_kruti_dev_text(text: str) -> bool:
        return bool(text and any(sig in text for sig in KRUTI_DEV_SIGNATURES))

    def _detect_kruti_dev_pdf(self, doc_pdf) -> bool:
        for page_num in range(min(3, len(doc_pdf))):
            if self._detect_kruti_dev_text(doc_pdf[page_num].get_text()):
                return True
        return False

    @staticmethod
    def _should_use_llamaparse(file_path: Path, force_ocr_for_doc: bool) -> bool:
        """Use LlamaParse for Hindi / Kruti Dev PDFs to conserve API credits."""
        if os.environ.get("LLAMAPARSE_ALL", "").strip() == "1":
            return True
        if force_ocr_for_doc:
            return True
        if "hindi" in file_path.name.lower():
            return True
        return False

    def _create_visual_ocr_pdf(self, doc_pdf, source_path: Path) -> Path:
        """Rasterize a Kruti Dev PDF for visual OCR. Saved outside the source PDF folder."""
        settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        temp_path = settings.PROCESSED_DIR / f".temp_ocr_{source_path.stem}.pdf"
        img_pdf = fitz.open()
        try:
            for page_num in range(len(doc_pdf)):
                page = doc_pdf[page_num]
                rect = page.rect
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                new_page = img_pdf.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(rect, stream=img_data)
            img_pdf.save(str(temp_path))
        finally:
            img_pdf.close()
        return temp_path

    @staticmethod
    def _cleanup_temp_pdf(temp_path: Path | None) -> None:
        if not temp_path:
            return
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception as e:
            print(f"   [Warning] Could not delete temp OCR file {temp_path.name}: {e}")

    def _remove_legacy_temp_pdfs(self, directory: Path) -> None:
        legacy = directory / "temp_visual_ocr.pdf"
        if legacy.exists():
            print(f"   [Cleanup] Removing legacy temp file from source folder: {legacy.name}")
            try:
                legacy.unlink()
            except Exception as e:
                print(f"   [Warning] Could not delete {legacy.name}: {e}")
    
    def split_documents_semantically(self, documents: list) -> list:
        import re
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        final_chunks = []
        for doc in documents:
            filename = doc.metadata.get("source", "").lower()
            # Decide if document is Legal or Procedural
            is_legal = any(x in filename for x in ["gfr", "rule", "manual_for_procurement", "vigilance", "cvc", "gem-manual"])
            
            content = doc.page_content
            
            if is_legal:
                # Matches rule boundaries in rules
                pattern = re.compile(
                    r'\n(?=(?:Rule\s+\d+|Rule-\d+|नियम\s+\d+|नियम-\d+)\b)',
                    re.IGNORECASE
                )
            else:
                # Matches Step boundaries or section headings in manuals
                pattern = re.compile(
                    r'\n(?=(?:Step\s+\d+|SECTION\s+\d+|\b\d+\.\d+(?:\.\d+)?\b)\b)',
                    re.IGNORECASE
                )
                
            parts = pattern.split(content)
            if len(parts) <= 1:
                parts = content.split("\n\n")
                
            for part in parts:
                part_trimmed = part.strip()
                if not part_trimmed:
                    continue
                    
                if len(part_trimmed) <= 2000:
                    final_chunks.append(Document(
                        page_content=part_trimmed,
                        metadata=doc.metadata
                    ))
                else:
                    temp_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=2000,
                        chunk_overlap=400,
                        separators=["\n\n", "\n", "। ", ". ", " ", ""],
                        length_function=len,
                    )
                    sub_docs = temp_splitter.create_documents([part_trimmed], [doc.metadata])
                    final_chunks.extend(sub_docs)
                    
        return final_chunks

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
        self._remove_legacy_temp_pdfs(directory)
        
        # Glob for pdf, docx, txt files (case-insensitive)
        files = set()
        for ext in ['*.pdf', '*.PDF', '*.docx', '*.DOCX', '*.txt', '*.TXT']:
            for f in directory.glob(ext):
                if not self._is_ingestion_skip_file(f):
                    files.add(f)  # Set automatically removes duplicates
        
        files = sorted(list(files))  # Convert back to sorted list
        
        if not files:
            print(f"   [Warning] No matching files found in {directory}")
            return []
        
        print(f"   [Files] Found {len(files)} file(s) in {directory.name}")
        
        for file_path in files:
            print(f"\n   [Processing] ({role}): {file_path.name}")
            
            ext = file_path.suffix.lower()
            chunks = []
            is_hindi_doc = False
            total_chars = 0
            
            if ext == '.pdf':
                api_key = os.environ.get("LLAMA_CLOUD_API_KEY") or os.environ.get("LLAMA_PARSE_API_KEY")
                parsed_with_llama = False
                temp_pdf_path = None
                
                if api_key:
                    doc_pdf = fitz.open(str(file_path))
                    try:
                        force_ocr_for_doc = self._detect_kruti_dev_pdf(doc_pdf)
                        use_llama = self._should_use_llamaparse(file_path, force_ocr_for_doc)

                        if not use_llama:
                            print(f"   [LlamaParse] Skipping {file_path.name} — English PDF, using local PyMuPDF extraction.")
                        else:
                            try:
                                pdf_to_parse = str(file_path)
                                if force_ocr_for_doc:
                                    print(f"   [LlamaParse] Detected legacy Kruti Dev font in {file_path.name}. Building visual OCR temp file...")
                                    temp_pdf_path = self._create_visual_ocr_pdf(doc_pdf, file_path)
                                    pdf_to_parse = str(temp_pdf_path)

                                print(f"   [LlamaParse] Extracting text page-by-page using LlamaParse for structured layout...")
                                from llama_parse import LlamaParse
                                doc_lang = "hi" if ("hindi" in file_path.name.lower() or force_ocr_for_doc) else "en"
                                parser = LlamaParse(
                                    api_key=api_key,
                                    result_type="markdown",
                                    language=doc_lang
                                )
                                llama_docs = parser.load_data(pdf_to_parse)

                                if "hindi" in file_path.name.lower() or force_ocr_for_doc:
                                    is_hindi_doc = True

                                for page_num, ldoc in enumerate(llama_docs, start=1):
                                    page_text = ldoc.text
                                    if not page_text or not page_text.strip():
                                        continue

                                    cleaned_page_text = self.clean_text(page_text)
                                    if cleaned_page_text.strip():
                                        total_chars += len(cleaned_page_text)
                                        page_doc = Document(
                                            page_content=cleaned_page_text,
                                            metadata={
                                                "source": file_path.name,
                                                "file_path": str(file_path),
                                                "role": role,
                                                "page": page_num,
                                                "file_size": file_path.stat().st_size,
                                                "processed_date": str(file_path.stat().st_mtime)
                                            }
                                        )
                                        page_marker = f"--- Page {page_num} ---\n"
                                        page_chunks = self.split_documents_semantically([page_doc])
                                        for pc in page_chunks:
                                            if "--- Page " not in pc.page_content:
                                                pc.page_content = page_marker + pc.page_content
                                            chunks.append(pc)

                                parsed_with_llama = True
                                print("   [LlamaParse] [Success] Structure extraction successful.")
                            except Exception as e:
                                print(f"   [LlamaParse] [Warning] Failed: {e}. Falling back to local PDF parser...")
                            finally:
                                self._cleanup_temp_pdf(temp_pdf_path)
                                temp_pdf_path = None
                    finally:
                        doc_pdf.close()
                
                if not parsed_with_llama:
                    # Local fallback using PyMuPDF + OCR page-by-page
                    try:
                        doc_pdf = fitz.open(str(file_path))
                        force_ocr_for_doc = self._detect_kruti_dev_pdf(doc_pdf)
                        
                        if force_ocr_for_doc:
                            print(f"   [Warning] Detected Kruti Dev/legacy Hindi font in {file_path.name}. Forcing OCR to extract Unicode text...")
                        
                        if "hindi" in file_path.name.lower() or force_ocr_for_doc:
                            is_hindi_doc = True
                        
                        # Extract page-by-page
                        for page_num in range(len(doc_pdf)):
                            page = doc_pdf[page_num]
                            page_text = page.get_text() if not force_ocr_for_doc else ""
                            cleaned_page_text = ""
                            
                            if page_text and page_text.strip():
                                filtered_page_text = self.filter_header_footer_lines(page_text, file_path.name)
                                cleaned_page_text = self.clean_layout_newlines(filtered_page_text)
                            else:
                                if os.environ.get("SKIP_OCR") != "1":
                                    ocr_reason = "has no text" if not force_ocr_for_doc else "forced due to legacy font"
                                    try:
                                        pix = page.get_pixmap(dpi=150)
                                        img_data = pix.tobytes("png")
                                        img = Image.open(io.BytesIO(img_data))
                                        
                                        page_text = pytesseract.image_to_string(img, lang='hin+eng')
                                        if page_text and page_text.strip():
                                            filtered_page_text = self.filter_header_footer_lines(page_text, file_path.name)
                                            cleaned_page_text = self.clean_layout_newlines(filtered_page_text)
                                        elif ocr_service.reader:
                                            page_text = ocr_service.extract_text_from_pdf_page(img)
                                            if page_text:
                                                filtered_page_text = self.filter_header_footer_lines(page_text, file_path.name)
                                                cleaned_page_text = self.clean_layout_newlines(filtered_page_text)
                                    except Exception as e:
                                        print(f"   OCR error on page {page_num + 1}: {e}")
                            
                            cleaned_page_text = self.clean_text(cleaned_page_text)
                            if cleaned_page_text.strip():
                                total_chars += len(cleaned_page_text)
                                # Create a document specifically for this page to preserve page number
                                page_doc = Document(
                                    page_content=cleaned_page_text,
                                    metadata={
                                        "source": file_path.name,
                                        "file_path": str(file_path),
                                        "role": role,
                                        "page": page_num + 1,
                                        "file_size": file_path.stat().st_size,
                                        "processed_date": str(file_path.stat().st_mtime)
                                    }
                                )
                                # Prepend page marker text
                                page_marker = f"--- Page {page_num + 1} ---\n"
                                
                                page_chunks = self.split_documents_semantically([page_doc])
                                for pc in page_chunks:
                                    if "--- Page " not in pc.page_content:
                                        pc.page_content = page_marker + pc.page_content
                                    chunks.append(pc)
                        doc_pdf.close()
                    except Exception as e:
                        print(f"   Error reading PDF {file_path.name}: {e}")
                        continue
                    
            elif ext in ['.docx', '.txt']:
                if ext == '.docx':
                    text, force_ocr_for_doc = self.extract_text_from_docx(str(file_path))
                else:
                    text, force_ocr_for_doc = self.extract_text_from_txt(str(file_path))
                
                if text.strip():
                    total_chars = len(text)
                    if "hindi" in file_path.name.lower() or force_ocr_for_doc or language_service.is_hindi_document(text):
                        is_hindi_doc = True
                    doc_obj = Document(
                        page_content=text,
                        metadata={
                            "source": file_path.name,
                            "file_path": str(file_path),
                            "role": role,
                            "file_size": file_path.stat().st_size,
                            "processed_date": str(file_path.stat().st_mtime)
                        }
                    )
                    chunks = self.split_documents_semantically([doc_obj])
            
            if not chunks:
                print(f"   [Warning] No text extracted from {file_path.name}")
                continue
                
            # Perform batch translation for Hindi chunks
            # English-named PDFs need a higher Devanagari threshold to avoid false positives
            filename_hints_hindi = "hindi" in file_path.name.lower()
            if not is_hindi_doc and chunks:
                sample_text = " ".join([c.page_content for c in chunks[:3]])
                threshold = 0.15 if filename_hints_hindi else 0.30
                if language_service.is_hindi_document(sample_text, threshold=threshold):
                    is_hindi_doc = True
                    if not filename_hints_hindi:
                        print(f"   [Info] Mixed Hindi/English content detected in {file_path.name}.")

            if is_hindi_doc:
                hindi_chunks = [c for c in chunks if language_service.is_hindi(c.page_content)]
                if not hindi_chunks and not filename_hints_hindi:
                    print(f"   [Info] No Hindi chunks found in {file_path.name} — keeping English text as-is.")
                    is_hindi_doc = False
                else:
                    translate_count = len(hindi_chunks) if hindi_chunks else len(chunks)
                    print(f"   [Hindi Document] Translating {translate_count} chunk(s) to English for vector indexing...")
                    chunk_texts = [chunk.page_content for chunk in chunks]
                    for chunk in chunks:
                        if language_service.is_hindi(chunk.page_content) or filename_hints_hindi:
                            chunk.metadata["original_hindi"] = chunk.page_content

                    translated_contents = language_service.translate_chunks_to_english(chunk_texts)
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
            print(f"   [Success] Created {len(chunks)} chunks (Total chars: {total_chars:,})")
        
        print(f"   [Total] TOTAL for {role}: {len(all_chunks)} chunks from {len(files)} files")
        return all_chunks

if __name__ == "__main__":
    processor = DocumentProcessor()
    
    vendor_chunks = processor.process_directory(settings.VENDOR_PDF_DIR, "vendor")
    govt_chunks = processor.process_directory(settings.GOVT_PDF_DIR, "government_officer")
    
    print(f"\n✅ Vendor chunks: {len(vendor_chunks)}")
    print(f"✅ Government chunks: {len(govt_chunks)}")