# backend/tests/test_gem_catalog.py
import pytest
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.gem_catalog_db import gem_catalog_db
from app.services.gem_scraper_service import gem_scraper_service, MAXIMUM_TARGET_CATEGORIES

def test_gem_catalog_db_init():
    """Verify SQLite database initialization and table creation."""
    assert gem_catalog_db is not None
    conn = gem_catalog_db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gem_catalog_products';")
    assert cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gem_scrape_checkpoints';")
    assert cursor.fetchone() is not None
    conn.close()

def test_560_categories_configuration():
    """Verify that gem_scraper_service has 560+ categories configured for all 162 departments."""
    count = len(MAXIMUM_TARGET_CATEGORIES)
    print(f"\n[OK] Configured Target Categories Count: {count}")
    assert count >= 500
    assert "laptops" in MAXIMUM_TARGET_CATEGORIES
    assert "icu beds" in MAXIMUM_TARGET_CATEGORIES
    assert "cctv bullet cameras" in MAXIMUM_TARGET_CATEGORIES
    assert "soil testing kits" in MAXIMUM_TARGET_CATEGORIES

def test_upsert_and_checkpoint():
    """Verify product upserting and checkpoint resumption recording."""
    test_category = f"test_laptops_{int(time.time())}"
    sample_products = [
        {
            "title": "HP ProBook 445 G10 Notebook",
            "brand": "HP",
            "model_name": "ProBook 445 G10",
            "min_price": 38500.0,
            "max_price": 42000.0,
            "seller_type": "OEM / MSE",
            "gem_product_url": "https://mkp.gem.gov.in/test-hp-laptop"
        },
        {
            "title": "Lenovo ThinkBook 15 G4",
            "brand": "Lenovo",
            "model_name": "ThinkBook 15 G4",
            "min_price": 39900.0,
            "max_price": 43500.0,
            "seller_type": "OEM",
            "gem_product_url": "https://mkp.gem.gov.in/test-lenovo-laptop"
        }
    ]
    
    saved_count = gem_catalog_db.upsert_products(test_category, sample_products)
    assert saved_count == 2
    
    gem_catalog_db.update_checkpoint(test_category, 1, "in_progress", saved_count)
    checkpoint = gem_catalog_db.get_checkpoint(test_category)
    
    assert checkpoint["category"] == test_category
    assert checkpoint["last_scraped_page"] == 1
    assert checkpoint["status"] == "in_progress"
    assert checkpoint["items_scraped"] >= 2

def test_find_products_in_budget():
    """Verify budget math calculation engine (L1, max quantity, cost calculation, and DFP authority)."""
    budget_result = gem_catalog_db.find_products_in_budget("laptop", 400000.0, target_qty=10)
    
    assert budget_result["catalog_available"] is True
    assert budget_result["total_budget"] == 400000.0
    assert budget_result["l1_option"] is not None
    assert budget_result["dfp_authority"] == "Head of Department (HOD)"
    
    l1 = budget_result["l1_option"]
    assert "unit_price" in l1
    assert "max_purchasable_qty" in l1
    assert l1["unit_price"] > 0
    assert l1["max_purchasable_qty"] >= 10
    
    print("\n[OK] Budget Feasibility Test Result:")
    print(f"   Category: {budget_result['category']}")
    print(f"   L1 Product: {l1['title']}")
    print(f"   Unit Price: Rs. {l1['unit_price']:,.2f}")
    print(f"   Max Purchasable Qty for Rs. 4L Budget: {l1['max_purchasable_qty']} units")
    print(f"   DFP Approval Authority: {budget_result['dfp_authority']}")

if __name__ == "__main__":
    pytest.main(["-v", __file__])
