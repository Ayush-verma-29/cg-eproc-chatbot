# scripts/check_indexed_chunks.py
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

from app.services.vector_store import VectorStoreManager

vsm = VectorStoreManager()
govt_store = vsm.get_govt_store()
vendor_store = vsm.get_vendor_store()

for name, store in [("Govt", govt_store), ("Vendor", vendor_store)]:
    print(f"\n=== Checking {name} Store ===")
    try:
        coll = store._collection
        # Get all metadata
        metadata_list = coll.get(include=["metadatas"])["metadatas"]
        
        # Count occurrences of each source
        source_counts = {}
        for m in metadata_list:
            src = m.get("source", "Unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
            
        print(f"Total chunks in collection: {len(metadata_list)}")
        print("Document breakdown in Chroma:")
        for src, count in sorted(source_counts.items()):
            print(f" - {src}: {count} chunks")
    except Exception as e:
        print(f"Error: {e}")
