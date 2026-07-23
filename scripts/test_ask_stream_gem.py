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
    query = "10 laptops for Rs 4 Lakhs budget"
    
    print(f"\n[Test] Calling engine.ask_stream('{query}')...")
    events = list(engine.ask_stream(question=query, role="government_officer"))
    
    full_text = "".join([e.get("text", "") for e in events if e.get("type") == "token"])
    
    assert "GeM L1 Price & Product Breakdown Matrix" in full_text
    assert "Rule 3.1.1" in full_text
    assert "Download Official GeM Financial Sanction Note (PDF)" in full_text
    
    print("\n✅ SUCCESS! ask_stream() intercepted budget query and returned full GeM Matrix:\n")
    print(full_text[:500])
    print("...")

if __name__ == "__main__":
    test_ask_stream_gem_interception()
