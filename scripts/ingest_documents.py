# scripts/ingest_documents.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreManager
from app.core.config import settings

def delete_all_data(force=False):
    """Delete all existing vector data"""
    if force:
        vsm = VectorStoreManager()
        vsm.delete_all_collections()
        print("✅ All vector stores deleted (forced).")
        return True
        
    print("\n⚠️ WARNING: This will delete ALL indexed documents!")
    confirm = input("Type 'DELETE ALL' to confirm: ")
    
    if confirm == "DELETE ALL":
        vsm = VectorStoreManager()
        vsm.delete_all_collections()
        print("✅ All vector stores deleted.")
        return True
    else:
        print("Cancelled.")
        return False

def main():
    print("=" * 70)
    print("  CG e-Procurement Chatbot - Document Ingestion")
    print("=" * 70)
    
    print(f"\n📁 Configuration:")
    print(f"   Vendor PDFs: {settings.VENDOR_PDF_DIR}")
    print(f"   Govt PDFs: {settings.GOVT_PDF_DIR}")
    print(f"   Chunk Size: {settings.CHUNK_SIZE} chars")
    print(f"   Overlap: {settings.CHUNK_OVERLAP} chars")
    
    processor = DocumentProcessor()
    vsm = VectorStoreManager()
    
    # Process Vendor Manuals
    print("\n" + "=" * 70)
    print("📄 STEP 1: Processing VENDOR Manuals")
    print("=" * 70)
    
    vendor_chunks = processor.process_directory(settings.VENDOR_PDF_DIR, "vendor")
    if vendor_chunks:
        print(f"\n💾 Adding {len(vendor_chunks)} vendor chunks to vector store...")
        vsm.add_vendor_documents(vendor_chunks)
    else:
        print("⚠️ No vendor chunks created")
    
    # Process Government Rules
    print("\n" + "=" * 70)
    print("📄 STEP 2: Processing GOVERNMENT Rules")
    print("=" * 70)
    
    govt_chunks = processor.process_directory(settings.GOVT_PDF_DIR, "government_officer")
    if govt_chunks:
        print(f"\n💾 Adding {len(govt_chunks)} government chunks to vector store...")
        vsm.add_govt_documents(govt_chunks)
    else:
        print("⚠️ No government chunks created")
    
    # VERIFY - Check if data was actually stored
    print("\n" + "=" * 70)
    print("📊 VERIFICATION - Checking Vector Store")
    print("=" * 70)
    
    stats = vsm.get_collection_stats()
    print(f"\n✅ Vendor documents: {stats.get('vendor_documents', 0)} chunks")
    print(f"✅ Government documents: {stats.get('govt_documents', 0)} chunks")
    
    # Check file sizes
    import os
    vendor_size = sum(f.stat().st_size for f in settings.VENDOR_DB_DIR.glob('*') if f.is_file()) / (1024 * 1024)
    govt_size = sum(f.stat().st_size for f in settings.GOVT_DB_DIR.glob('*') if f.is_file()) / (1024 * 1024)
    
    print(f"\n💾 Database file sizes:")
    print(f"   Vendor DB: {vendor_size:.2f} MB")
    print(f"   Govt DB: {govt_size:.2f} MB")
    
    if govt_size < 1:
        print("\n⚠️ WARNING: Govt DB is very small! Chunks may not have been stored correctly.")
        print("   Check that your PDFs have extractable text.")
    
    print("\n" + "=" * 70)
    if stats.get('govt_documents', 0) > 0:
        print("🎉 INGESTION SUCCESSFUL!")
        print("\nStart the API server:")
        print("   uvicorn backend.app.main:app --reload --port 8001")
    else:
        print("⚠️ INGESTION FAILED - No documents in vector store")
        print("   Check that your PDFs are not empty or password protected")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reindex", action="store_true", help="Delete all data and reindex")
    parser.add_argument("--force", action="store_true", help="Bypass confirmation prompt when reindexing")
    args = parser.parse_args()
    
    if args.reindex:
        if delete_all_data(force=args.force):
            main()
    else:
        main()