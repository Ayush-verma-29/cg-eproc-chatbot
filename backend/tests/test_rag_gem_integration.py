# backend/tests/test_rag_gem_integration.py
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


from app.core.rag_engine import get_rag_engine
from app.services.sanction_pdf_service import SANCTION_DIR

def test_rag_gem_budget_query_evaluation():
    """Verify RAG Engine interception for budget queries, L1 matrix generation, DFP authority, and PDF creation."""
    engine = get_rag_engine()
    test_query = "Our department has a budget of 4 Lakhs for 10 laptops. How should we proceed?"
    
    response = engine.evaluate_gem_budget_query(test_query)
    
    assert response is not None
    assert "GeM L1 Price & Product Breakdown Matrix" in response
    assert "Head of Department (HOD)" in response
    assert "Rule 3.1.1" in response
    assert "Download Official GeM Financial Sanction Note (PDF)" in response
    
    print("\n[OK] Integrated RAG Response Preview:")
    print(response[:600])

def test_pdf_sanction_note_generation():
    """Verify that Sanction PDF notes are saved into the sanction_notes directory."""
    assert SANCTION_DIR.exists()
    pdf_files = list(SANCTION_DIR.glob("*.pdf"))
    assert len(pdf_files) > 0
    print(f"\n[OK] Verified {len(pdf_files)} generated Sanction Note PDF file(s) in {SANCTION_DIR}")

if __name__ == "__main__":
    pytest.main(["-v", __file__])
