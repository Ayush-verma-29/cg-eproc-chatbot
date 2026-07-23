# scripts/test_ask_stream_gem.py
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from app.core.rag_engine import get_rag_engine

def test_ask_stream_gem_interception():
    engine = get_rag_engine()
    
    test_queries = [
        "10 laptops for Rs 4 Lakhs budget",
        "10 table for Rs 4 Lakhs budget",
        "20 chairs for 1.5 Lakhs budget",
        "5 printers for 80,000 rupees"
    ]
    
    print("\n======================================================================")
    print("      TESTING ASK_STREAM INTERCEPTION WITH UNIVERSAL STEMMING         ")
    print("======================================================================\n")
    
    for q in test_queries:
        print(f"🔹 Testing Query: '{q}'")
        events = list(engine.ask_stream(question=q, role="government_officer"))
        full_text = "".join([e.get("text", "") for e in events if e.get("type") == "token"])
        
        assert "GeM L1 Price & Product Breakdown Matrix" in full_text, f"Failed matrix match for '{q}'"
        assert "Rule 3.1.1" in full_text, f"Failed Rule 3.1.1 match for '{q}'"
        assert "Download Official GeM Financial Sanction Note (PDF)" in full_text, f"Failed PDF match for '{q}'"
        
        print(f"   ✅ Instant GeM Matrix Matched! Snippet:")
        first_line = full_text.split('\n')[0]
        print(f"      {first_line}")
        print("   ------------------------------------------------------------------\n")

if __name__ == "__main__":
    test_ask_stream_gem_interception()
