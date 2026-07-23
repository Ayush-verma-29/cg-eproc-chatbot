# backend/app/services/gem_catalog_db.py
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings

DB_PATH = settings.DATA_DIR / "gem_catalog.db"

class GeMCatalogDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize SQLite tables for GeM Catalog products and Scraper Checkpoints."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Product Catalog Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS gem_catalog_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(100) NOT NULL,
                title TEXT NOT NULL,
                brand VARCHAR(100),
                model_name VARCHAR(150),
                min_price REAL NOT NULL,
                max_price REAL,
                currency VARCHAR(10) DEFAULT 'INR',
                specifications TEXT,
                seller_type VARCHAR(50) DEFAULT 'OEM',
                in_stock BOOLEAN DEFAULT 1,
                gem_product_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, title, brand) ON CONFLICT REPLACE
            );
            """)

            # 2. Category & Price Index
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gem_category_price 
            ON gem_catalog_products(category, min_price);
            """)

            # 3. Scrape Checkpoint Table (for Resumption)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS gem_scrape_checkpoints (
                category VARCHAR(100) PRIMARY KEY,
                last_scraped_page INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'in_progress',
                items_scraped INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

    def upsert_products(self, category: str, products: List[Dict[str, Any]]) -> int:
        """Bulk insert/replace products into SQLite database."""
        if not products:
            return 0
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for item in products:
                specs_json = json.dumps(item.get("specifications", {}), ensure_ascii=False)
                cursor.execute("""
                INSERT OR REPLACE INTO gem_catalog_products 
                (category, title, brand, model_name, min_price, max_price, currency, specifications, seller_type, in_stock, gem_product_url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    category.lower(),
                    item.get("title", "GeM Product"),
                    item.get("brand", "Generic"),
                    item.get("model_name", item.get("title", "")),
                    float(item.get("min_price", 0.0)),
                    float(item.get("max_price", item.get("min_price", 0.0))),
                    item.get("currency", "INR"),
                    specs_json,
                    item.get("seller_type", "OEM"),
                    1 if item.get("in_stock", True) else 0,
                    item.get("gem_product_url", "https://mkp.gem.gov.in"),
                    datetime.utcnow().isoformat()
                ))
                count += 1
            conn.commit()
            return count

    def get_checkpoint(self, category: str) -> Dict[str, Any]:
        """Fetch the checkpoint status and last scraped page for a category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gem_scrape_checkpoints WHERE category = ?", (category.lower(),))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {"category": category.lower(), "last_scraped_page": 0, "status": "not_started", "items_scraped": 0}

    def update_checkpoint(self, category: str, page: int, status: str, items_added: int):
        """Update scrape progress for a category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO gem_scrape_checkpoints
            (category, last_scraped_page, status, items_scraped, updated_at)
            VALUES (?, ?, ?, COALESCE((SELECT items_scraped FROM gem_scrape_checkpoints WHERE category = ?), 0) + ?, ?)
            """, (category.lower(), page, status, category.lower(), items_added, datetime.utcnow().isoformat()))
            conn.commit()

    def find_products_in_budget(
        self, 
        category: str, 
        total_budget: float, 
        target_qty: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query available GeM items within total budget.
        Calculates L1, L2, L3 options, max quantity, and MSE waivers.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cat_query = f"%{category.lower().rstrip('s')}%"
            
            cursor.execute("""
            SELECT * FROM gem_catalog_products 
            WHERE category LIKE ? AND in_stock = 1 AND min_price > 0
            ORDER BY min_price ASC
            LIMIT 10
            """, (cat_query,))
            
            rows = [dict(r) for r in cursor.fetchall()]
            
            if not rows:
                return self._generate_fallback_budget_estimate(category, total_budget, target_qty)

            matches = []
            for rank, r in enumerate(rows[:3], start=1):
                unit_price = float(r["min_price"])
                max_qty = int(total_budget // unit_price) if unit_price > 0 else 0
                
                req_qty = target_qty if target_qty and target_qty > 0 else max_qty
                total_cost = unit_price * req_qty
                
                fits_budget = total_cost <= total_budget
                
                matches.append({
                    "rank": f"L{rank}",
                    "title": r["title"],
                    "brand": r["brand"],
                    "model": r["model_name"],
                    "unit_price": unit_price,
                    "max_purchasable_qty": max_qty,
                    "calculated_total_cost": total_cost,
                    "target_qty_fits": fits_budget,
                    "seller_type": r["seller_type"],
                    "mse_eligible": r["seller_type"] in ["MSE", "OEM"],
                    "gem_url": r["gem_product_url"]
                })

            l1_item = matches[0] if matches else None
            dfp_info = self.get_dfp_approval_authority(total_budget)
            pac_alert = self.check_pac_single_supplier(category, len(rows))
            
            return {
                "category": category,
                "total_budget": total_budget,
                "target_qty": target_qty,
                "catalog_available": True,
                "l1_option": l1_item,
                "comparative_matrix": matches,
                "dfp_authority": dfp_info["authority"],
                "dfp_description": dfp_info["description"],
                "pac_alert": pac_alert,
                "single_supplier_detected": len(rows) == 1,
                "total_items_matched": len(rows)
            }

    def get_dfp_approval_authority(self, total_budget: float) -> Dict[str, str]:
        """Calculates delegated financial power sanction authority based on purchase value."""
        if total_budget <= 50000.0:
            return {
                "authority": "Head of Office (HOO)",
                "description": "Direct Purchase permitted under Delegated Financial Powers up to ₹50,000."
            }
        elif total_budget <= 500000.0:
            return {
                "authority": "Head of Department (HOD)",
                "description": "Financial Sanction delegated to HOD for procurements up to ₹5 Lakhs."
            }
        elif total_budget <= 2000000.0:
            return {
                "authority": "Administrative Department (Secretariat)",
                "description": "Requires Financial Sanction from Administrative Department Secretary (₹5L to ₹20L)."
            }
        else:
            return {
                "authority": "Finance Department (FD Concurrence Required)",
                "description": "Requires Finance Department written concurrence & Minister Approval (> ₹20 Lakhs)."
            }

    def check_pac_single_supplier(self, category: str, item_count: int) -> Optional[Dict[str, str]]:
        """Triggers Rule 4.3.1 alert if only 1 supplier/brand matches specification on GeM."""
        if item_count == 1:
            return {
                "rule": "Rule 4.3.1 (Parishisht 4)",
                "title": "Proprietary Article Certificate (PAC) Warning",
                "message": f"Single supplier detected on GeM for '{category}'. Procuring this item requires a Proprietary Article Certificate (PAC - Parishisht 4) and a mandatory 30-day public objection notice under Rule 4.3.1."
            }
        return None

    def detect_order_splitting(self, purchase_history: List[float], new_amount: float) -> Optional[Dict[str, str]]:
        """Detects piecemeal order splitting to evade open tender thresholds (Rule 4.13 / GFR 149)."""
        recent_sub_50k = [amt for amt in purchase_history if amt <= 50000.0]
        if new_amount <= 50000.0 and len(recent_sub_50k) >= 2:
            total_combined = sum(recent_sub_50k) + new_amount
            if total_combined > 50000.0:
                return {
                    "rule": "Rule 4.13 & GFR 149",
                    "title": "Compliance Fraud Alert: Order Splitting Prohibition",
                    "message": f"Splitting a single requirement into multiple repeat sub-₹50,000 purchase orders is prohibited under Rule 4.13. Combined purchases total ₹{total_combined:,.2f}, which exceeds the Direct Purchase threshold and requires L1 Quotation / Open Tender."
                }
        return None

    def _generate_fallback_budget_estimate(
        self, 
        category: str, 
        total_budget: float, 
        target_qty: Optional[int]
    ) -> Dict[str, Any]:
        """Provides realistic benchmark estimations when GeM DB is building initial cache."""
        category_base_prices = {
            "laptop": 38500.0,
            "desktop": 32000.0,
            "printer": 14500.0,
            "copier": 85000.0,
            "furniture": 6500.0
        }
        
        cat_key = next((k for k in category_base_prices if k in category.lower()), "laptop")
        base_p = category_base_prices[cat_key]
        
        l1_p = base_p
        l2_p = base_p * 1.05
        l3_p = base_p * 1.12
        
        matrix = []
        brands = [("HP", "ProBook Series", "OEM / MSE"), ("Lenovo", "ThinkCentre Series", "OEM"), ("Dell", "Vostro Series", "Authorized Reseller")]
        prices = [l1_p, l2_p, l3_p]
        
        for idx, ((b, m, st), p) in enumerate(zip(brands, prices), start=1):
            max_q = int(total_budget // p)
            req_q = target_qty if target_qty else max_q
            matrix.append({
                "rank": f"L{idx}",
                "title": f"{b} Commercial {category.capitalize()} ({m})",
                "brand": b,
                "model": m,
                "unit_price": p,
                "max_purchasable_qty": max_q,
                "calculated_total_cost": p * req_q,
                "target_qty_fits": (p * req_q) <= total_budget,
                "seller_type": st,
                "mse_eligible": "MSE" in st or "OEM" in st,
                "gem_url": "https://mkp.gem.gov.in"
            })
            
        return {
            "category": category,
            "total_budget": total_budget,
            "target_qty": target_qty,
            "catalog_available": True,
            "indicative_estimate": True,
            "l1_option": matrix[0],
            "comparative_matrix": matrix,
            "single_supplier_detected": False,
            "total_items_matched": 3
        }

gem_catalog_db = GeMCatalogDB()
