# scripts/ingest_documents.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreManager
from app.core.config import settings

def delete_all_data(force=False, role="all"):
    """Delete vector data for all roles or a single role."""
    role = normalize_role(role)
    if role == "all":
        label = "ALL indexed documents"
    elif role == "vendor":
        label = "ALL VENDOR indexed documents"
    else:
        label = "ALL GOVERNMENT indexed documents"

    if not force:
        print(f"\n⚠️ WARNING: This will delete {label}!")
        confirm = input("Type 'DELETE ALL' to confirm: ")
        if confirm != "DELETE ALL":
            print("Cancelled.")
            return False

    vsm = VectorStoreManager()
    if role in ("all", "vendor"):
        try:
            vsm.get_vendor_store().delete_collection()
            print("✅ Vendor collection deleted.")
        except Exception as e:
            print(f"⚠️ Error deleting vendor collection: {e}")
        vsm.vendor_store = None

    if role in ("all", "government_officer"):
        try:
            vsm.get_govt_store().delete_collection()
            print("✅ Government collection deleted.")
        except Exception as e:
            print(f"⚠️ Error deleting government collection: {e}")
        vsm.govt_store = None

    if role == "all":
        print("✅ All vector stores deleted.")
    return True


def normalize_role(role: str) -> str:
    role = (role or "all").strip().lower()
    aliases = {
        "govt": "government_officer",
        "government": "government_officer",
        "government_officer": "government_officer",
        "officer": "government_officer",
        "vendor": "vendor",
        "all": "all",
    }
    if role not in aliases:
        raise ValueError(
            f"Invalid role '{role}'. Use: all, vendor, government_officer (or govt)"
        )
    return aliases[role]


def print_preflight(role: str):
    """Print environment checks before ingestion."""
    role = normalize_role(role)
    print("\n🔎 Pre-flight checks:")
    llama_key = os.environ.get("LLAMA_CLOUD_API_KEY") or os.environ.get("LLAMA_PARSE_API_KEY")
    if llama_key:
        print("   ✅ LlamaParse API key found (Hindi/Kruti Dev PDFs will use LlamaParse)")
    else:
        print("   ⚠️  No LlamaParse API key — set LLAMA_CLOUD_API_KEY for Hindi PDF extraction")

    if role in ("all", "government_officer"):
        govt_dir = settings.GOVT_PDF_DIR
        pdfs = sorted(
            f for f in govt_dir.glob("*")
            if f.is_file() and f.suffix.lower() == ".pdf" and f.name.lower() != "temp_visual_ocr.pdf"
        )
        hindi_pdfs = [f.name for f in pdfs if "hindi" in f.name.lower()]
        print(f"   📄 Government PDFs to ingest: {len(pdfs)}")
        if hindi_pdfs:
            print(f"   🌐 Hindi PDFs (LlamaParse + Google Translate): {len(hindi_pdfs)}")
            for name in hindi_pdfs:
                print(f"      - {name}")
        legacy_temp = govt_dir / "temp_visual_ocr.pdf"
        if legacy_temp.exists():
            print(f"   ⚠️  Legacy temp file will be auto-removed: {legacy_temp.name}")


def main(role="all"):
    print("=" * 70)
    print("  CG e-Procurement Chatbot - Document Ingestion")
    print("=" * 70)
    
    print(f"\n📁 Configuration:")
    print(f"   Vendor PDFs: {settings.VENDOR_PDF_DIR}")
    print(f"   Govt PDFs: {settings.GOVT_PDF_DIR}")
    print(f"   Chunk Size: {settings.CHUNK_SIZE} chars")
    print(f"   Overlap: {settings.CHUNK_OVERLAP} chars")
    print_preflight(role)
    
    role = normalize_role(role)
    processor = DocumentProcessor()
    vsm = VectorStoreManager()

    vendor_chunks = []
    govt_chunks = []

    if role in ("all", "vendor"):
        print("\n" + "=" * 70)
        print("📄 Processing VENDOR Manuals")
        print("=" * 70)

        vendor_chunks = processor.process_directory(settings.VENDOR_PDF_DIR, "vendor")
        if vendor_chunks:
            print(f"\n💾 Adding {len(vendor_chunks)} vendor chunks to vector store...")
            vsm.add_vendor_documents(vendor_chunks)
        else:
            print("⚠️ No vendor chunks created")

    if role in ("all", "government_officer"):
        print("\n" + "=" * 70)
        print("📄 Processing GOVERNMENT Rules")
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
    
    if role in ("all", "government_officer") and govt_size < 1:
        print("\n⚠️ WARNING: Govt DB is very small! Chunks may not have been stored correctly.")
        print("   Check that your PDFs have extractable text.")

    print("\n" + "=" * 70)
    success = True
    if role in ("all", "vendor") and not vendor_chunks and role != "all":
        success = False
    if role in ("all", "government_officer") and stats.get("govt_documents", 0) == 0:
        if role == "government_officer":
            success = False
        elif role == "all":
            success = stats.get("govt_documents", 0) > 0 or stats.get("vendor_documents", 0) > 0

    if success:
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
    parser.add_argument(
        "--role",
        default="all",
        choices=["all", "vendor", "government_officer", "govt"],
        help="Ingest only vendor, only government, or all (default: all)",
    )
    parser.add_argument("--reindex", action="store_true", help="Delete existing index data before ingesting")
    parser.add_argument("--force", action="store_true", help="Bypass confirmation prompt when reindexing")
    args = parser.parse_args()

    if args.reindex:
        if delete_all_data(force=args.force, role=args.role):
            main(role=args.role)
    else:
        main(role=args.role)