# scripts/ingest_incremental.py
import sys
from pathlib import Path

# Setup encoding for Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreManager
from app.core.language import language_service
from langchain.schema import Document

def process_single_file(file_path: Path, role: str, processor: DocumentProcessor, source_override: str = None) -> list:
    print(f"\n📑 Processing ({role}): {file_path.name}")
    if not file_path.exists():
        print(f"❌ Error: File {file_path} does not exist!")
        return []
        
    ext = file_path.suffix.lower()
    if ext == '.pdf':
        text, force_ocr_for_doc = processor.extract_text_from_pdf(str(file_path))
    elif ext == '.docx':
        text, force_ocr_for_doc = processor.extract_text_from_docx(str(file_path))
    elif ext in ('.txt', '.md'):
        text, force_ocr_for_doc = processor.extract_text_from_txt(str(file_path))
    else:
        text, force_ocr_for_doc = "", False
        
    if not text.strip():
        print(f"   ⚠️ Warning: No text extracted from {file_path.name}")
        return []
        
    source_name = source_override if source_override else file_path.name
    
    # Create document with role metadata
    doc = Document(
        page_content=text,
        metadata={
            "source": source_name,
            "file_path": str(file_path),
            "role": role,
            "file_size": file_path.stat().st_size,
            "processed_date": str(file_path.stat().st_mtime)
        }
    )
    
    chunks = processor.split_documents_semantically([doc])
    
    # Determine if Hindi document based on filename, forced OCR, or character density
    is_hindi_doc = False
    if "hindi" in file_path.name.lower():
        is_hindi_doc = True
    elif force_ocr_for_doc:
        is_hindi_doc = True
    elif language_service.is_hindi_document(text):
        is_hindi_doc = True
        
    if is_hindi_doc:
        print(f"   🌐 Document detected as Hindi. Translating {len(chunks)} chunks to English for vector indexing...")
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
        if is_hindi_doc:
            chunk.metadata["language"] = "hi"
            
    print(f"   ✅ Created {len(chunks)} chunks (Total chars: {len(text):,})")
    return chunks

def main():
    print("=" * 70)
    print("  CG e-Procurement Chatbot - Incremental Ingestion")
    print("=" * 70)
    
    processor = DocumentProcessor()
    vsm = VectorStoreManager()
    
    # Files to ingest
    vendor_files = [
        (Path("backend/data/vendor_manuals/faq.txt"), None),
        (Path("backend/data/vendor_manuals/FAQ_CHiPS_Online_EMD_V2.0.docx"), None)
    ]
    
    govt_files = [
        (Path("backend/data/govt_rules/Précis  e-Procurement Project.docx"), "Précis  e-Procurement Project.docx"),
        (Path("backend/data/govt_rules/portal_operations_manual.md"), "portal_operations_manual.md")
    ]
    
    # Process and add Vendor Files
    vendor_chunks_to_add = []
    for file_path, override_name in vendor_files:
        chunks = process_single_file(file_path, "vendor", processor, override_name)
        vendor_chunks_to_add.extend(chunks)
        
    if vendor_chunks_to_add:
        print(f"\n💾 Adding {len(vendor_chunks_to_add)} vendor chunks to Chroma vendor store...")
        vsm.add_vendor_documents(vendor_chunks_to_add)
        print("✅ Added to vendor store.")
        
    # Process and add Govt Files
    govt_chunks_to_add = []
    for file_path, override_name in govt_files:
        chunks = process_single_file(file_path, "government_officer", processor, override_name)
        govt_chunks_to_add.extend(chunks)
        
    if govt_chunks_to_add:
        print(f"\n💾 Adding {len(govt_chunks_to_add)} government chunks to Chroma govt store...")
        vsm.add_govt_documents(govt_chunks_to_add)
        print("✅ Added to govt store.")
        
    print("\n" + "=" * 70)
    print("📊 VERIFICATION")
    print("=" * 70)
    stats = vsm.get_collection_stats()
    print(f"Total Vendor store chunks: {stats.get('vendor_documents', 0)}")
    print(f"Total Government store chunks: {stats.get('govt_documents', 0)}")
    print("Incremental ingestion complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
