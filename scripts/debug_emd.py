# scripts/debug_emd.py
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.core.rag_engine import RAGEngine
from app.services.vector_store import VectorStoreManager

print("Initializing VectorStoreManager...")
vsm = VectorStoreManager()
stats = vsm.get_collection_stats()
print(f"Stats: {stats}")

print("Initializing RAGEngine...")
re = RAGEngine()
re.initialize()

print("Dynamic sources list loaded in RAGEngine:")
print(re.known_sources)

print("\nTesting retrieve_chunks for query 'EMD' (role: vendor):")
chunks = re.retrieve_chunks("EMD", "vendor")
print(f"Number of chunks retrieved: {len(chunks)}")
for idx, c in enumerate(chunks):
    print(f"Chunk {idx+1}:")
    print(f"  Source: {c.get('source')}")
    print(f"  Score: {c.get('score')}")
    print(f"  Content snippet: {c.get('content')[:120]}...")

print("\nTesting get_query_sources for query 'EMD' (role: vendor):")
sources_data = re.get_query_sources("EMD", "vendor", "en")
print(sources_data)
