# backend/app/services/sanction_pdf_service.py
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from app.core.config import settings

SANCTION_DIR = settings.DATA_DIR / "sanction_notes"
SANCTION_DIR.mkdir(parents=True, exist_ok=True)

class SanctionPDFService:
    def __init__(self, output_dir: Path = SANCTION_DIR):
        self.output_dir = output_dir

    def generate_sanction_note_pdf(self, data: Dict[str, Any]) -> str:
        """Generates an official downloadable GeM Financial Sanction Note (PDF)."""
        category = data.get("category", "Office Procurement").title()
        total_budget = float(data.get("total_budget", 0.0))
        target_qty = data.get("target_qty", "N/A")
        dfp_authority = data.get("dfp_authority", "Head of Department (HOD)")
        rule_citation = data.get("rule_citation", "Rule 3.1.1 & Rule 4.7(अ) of CG Store Purchase Rules")
        l1_option = data.get("l1_option", {})
        
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 Size
        
        # Colors & Layout
        navy = (0.1, 0.2, 0.45)
        dark_gray = (0.2, 0.2, 0.2)
        green = (0.1, 0.5, 0.2)
        
        # Header Banner
        page.draw_rect(fitz.Rect(0, 0, 595, 80), color=navy, fill=navy)
        page.insert_text(fitz.Point(40, 45), "GOVERNMENT OF CHHATTISGARH", fontsize=16, color=(1, 1, 1), fontname="helvetica-bold")
        page.insert_text(fitz.Point(40, 65), "OFFICIAL FINANCIAL SANCTION NOTE & AVAILABILITY CERTIFICATE", fontsize=11, color=(0.9, 0.9, 0.9), fontname="helvetica")
        
        # Metadata Block
        now_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        sanction_ref = f"CG-PROC/{datetime.now().strftime('%Y%m%d')}/{int(datetime.now().timestamp()) % 10000}"
        
        y = 110
        page.insert_text(fitz.Point(40, y), f"Sanction Reference: {sanction_ref}", fontsize=10, fontname="helvetica-bold", color=dark_gray)
        page.insert_text(fitz.Point(380, y), f"Date: {now_str}", fontsize=10, fontname="helvetica", color=dark_gray)
        
        y += 25
        page.draw_line(fitz.Point(40, y), fitz.Point(555, y), color=(0.8, 0.8, 0.8), width=1)
        
        # Section 1: Subject & Department Details
        y += 30
        page.insert_text(fitz.Point(40, y), "1. SUBJECT & PROCUREMENT SUMMARY", fontsize=12, fontname="helvetica-bold", color=navy)
        
        y += 20
        page.insert_text(fitz.Point(55, y), f"• Procurement Category: {category}", fontsize=10, fontname="helvetica", color=dark_gray)
        y += 18
        page.insert_text(fitz.Point(55, y), f"• Total Approved Budget: Rs. {total_budget:,.2f}", fontsize=10, fontname="helvetica-bold", color=dark_gray)
        y += 18
        page.insert_text(fitz.Point(55, y), f"• Target Quantity: {target_qty} Units", fontsize=10, fontname="helvetica", color=dark_gray)
        y += 18
        page.insert_text(fitz.Point(55, y), f"• Mandatory Procurement Channel: Government e-Marketplace (GeM Portal)", fontsize=10, fontname="helvetica", color=dark_gray)
        
        # Section 2: Verified GeM L1 Product Breakdown
        y += 30
        page.insert_text(fitz.Point(40, y), "2. VERIFIED GeM CATALOG L1 PRICE BREAKDOWN", fontsize=12, fontname="helvetica-bold", color=navy)
        
        y += 15
        # Table Header Box
        page.draw_rect(fitz.Rect(40, y, 555, y + 22), color=navy, fill=(0.92, 0.94, 0.98))
        page.insert_text(fitz.Point(50, y + 15), "Rank", fontsize=9, fontname="helvetica-bold", color=navy)
        page.insert_text(fitz.Point(90, y + 15), "Product Title & Brand", fontsize=9, fontname="helvetica-bold", color=navy)
        page.insert_text(fitz.Point(310, y + 15), "Unit Price", fontsize=9, fontname="helvetica-bold", color=navy)
        page.insert_text(fitz.Point(400, y + 15), "Purchasable Qty", fontsize=9, fontname="helvetica-bold", color=navy)
        page.insert_text(fitz.Point(495, y + 15), "Seller Category", fontsize=9, fontname="helvetica-bold", color=navy)
        
        y += 22
        matrix = data.get("comparative_matrix", [])
        for item in matrix[:3]:
            page.draw_rect(fitz.Rect(40, y, 555, y + 20), color=(0.85, 0.85, 0.85), fill=None)
            page.insert_text(fitz.Point(50, y + 14), str(item.get("rank", "L1")), fontsize=9, fontname="helvetica-bold", color=green if item.get("rank") == "L1" else dark_gray)
            page.insert_text(fitz.Point(90, y + 14), str(item.get("title", ""))[:32], fontsize=8, fontname="helvetica", color=dark_gray)
            page.insert_text(fitz.Point(310, y + 14), f"Rs. {item.get('unit_price', 0):,.2f}", fontsize=8, fontname="helvetica", color=dark_gray)
            page.insert_text(fitz.Point(415, y + 14), f"{item.get('max_purchasable_qty', 0)} Units", fontsize=8, fontname="helvetica", color=dark_gray)
            page.insert_text(fitz.Point(495, y + 14), str(item.get("seller_type", "OEM"))[:10], fontsize=8, fontname="helvetica", color=dark_gray)
            y += 20

        # Section 3: Compliance & Approval Authority
        y += 25
        page.insert_text(fitz.Point(40, y), "3. STATUTORY COMPLIANCE & SANCTION AUTHORITY", fontsize=12, fontname="helvetica-bold", color=navy)
        
        y += 20
        page.insert_text(fitz.Point(55, y), f"• Sanctioning Authority: {dfp_authority} under CG Delegated Financial Powers.", fontsize=10, fontname="helvetica-bold", color=dark_gray)
        y += 18
        page.insert_text(fitz.Point(55, y), f"• Rule Reference: {rule_citation}.", fontsize=10, fontname="helvetica", color=dark_gray)
        y += 18
        page.insert_text(fitz.Point(55, y), "• MSE Benefit: Qualified for MSE EMD Waiver & 15% Price Preference.", fontsize=10, fontname="helvetica", color=dark_gray)
        
        # Signatures Block
        y += 100
        page.draw_line(fitz.Point(50, y), fitz.Point(200, y), color=dark_gray, width=1)
        page.draw_line(fitz.Point(380, y), fitz.Point(530, y), color=dark_gray, width=1)
        
        y += 15
        page.insert_text(fitz.Point(60, y), "Prepared By (Operator)", fontsize=9, fontname="helvetica", color=dark_gray)
        page.insert_text(fitz.Point(385, y), f"Approved By ({dfp_authority})", fontsize=9, fontname="helvetica-bold", color=navy)
        
        filename = f"Financial_Sanction_Note_{int(datetime.now().timestamp())}.pdf"
        output_path = self.output_dir / filename
        doc.save(str(output_path))
        doc.close()
        
        return f"/api/v1/download-sanction-pdf/{filename}"

sanction_pdf_service = SanctionPDFService()
