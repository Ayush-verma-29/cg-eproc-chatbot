# scripts/check_gfr_emd.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.vector_store import VectorStoreManager

# Unicode/Emoji safe print helper
def get_safe_symbol(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'ascii')
        return emoji
    except Exception:
        return fallback

OK_SYM = get_safe_symbol("✅", "[OK]")

vsm = VectorStoreManager()
govt_store = vsm.get_govt_store()

# Search specifically for GFR documents
results = govt_store.similarity_search("Rule 170 Bid Security", k=5)

print("Search results for 'Rule 170 Bid Security':")
for doc in results:
    source = doc.metadata.get('source', 'Unknown')
    if "GFR" in source or "Final_GFR" in source:
        print(f"\n{OK_SYM} FOUND in: {source}")
        # Extract around Rule 170
        text = doc.page_content
        if "Rule 170" in text:
            idx = text.find("Rule 170")
            print(text[idx:idx+300])
    else:
        print(f"   Other: {source}")