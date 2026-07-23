"""
Generate Styled Project README PDF from User Text
==================================================
Formats and renders the exact project description, key features,
setup commands, and test instructions into a high-quality, professional PDF.
"""
import sys
from pathlib import Path
from datetime import datetime

# ReportLab PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

OUTPUT_PDF = Path("readme.pdf")

def main():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_title = ParagraphStyle(
        "DocTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1a3c5e"),
        spaceAfter=6, alignment=TA_CENTER, leading=28,
        fontName="Helvetica-Bold"
    )
    style_subtitle = ParagraphStyle(
        "DocSub", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#555555"),
        spaceAfter=15, alignment=TA_CENTER,
        fontName="Helvetica-Oblique"
    )
    style_h1 = ParagraphStyle(
        "Heading1", parent=styles["Heading1"],
        fontSize=13, textColor=colors.HexColor("#1a3c5e"),
        spaceBefore=14, spaceAfter=8,
        fontName="Helvetica-Bold",
        keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        "Heading2", parent=styles["Heading2"],
        fontSize=10.5, textColor=colors.HexColor("#333333"),
        spaceBefore=10, spaceAfter=4,
        fontName="Helvetica-Bold",
        keepWithNext=True
    )
    style_body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=9.5, leading=14, spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
    )
    style_bullet = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontSize=9.5, leading=13.5, spaceAfter=4,
        leftIndent=15,
        fontName="Helvetica",
    )
    style_bullet_2 = ParagraphStyle(
        "Bullet2", parent=styles["Normal"],
        fontSize=9, leading=13, spaceAfter=3,
        leftIndent=30,
        fontName="Helvetica",
    )
    style_code = ParagraphStyle(
        "CodeBlock", parent=styles["Normal"],
        fontSize=8.5, leading=11, spaceAfter=8,
        fontName="Courier",
        textColor=colors.HexColor("#24292e"),
        backColor=colors.HexColor("#f6f8fa"),
        borderPadding=6,
        leftIndent=10,
        rightIndent=10
    )

    story = []

    # ── Header ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("CG e-Procurement Chatbot", style_title))
    story.append(Paragraph("Project Architecture & Deployment Guide", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3c5e"), spaceAfter=12))

    # Intro Description
    story.append(Paragraph(
        "An AI-powered Retrieval-Augmented Generation (RAG) assistant designed for the "
        "<b>Chhattisgarh e-Procurement Portal</b>. The chatbot helps users (Vendors/Contractors "
        "and Government Officers) query procurement manuals, General Financial Rules (GFR), and "
        "CVC compliance guidelines in English, Hindi, and Hinglish.", 
        style_body
    ))
    story.append(Spacer(1, 0.2*cm))

    # ── Key Features ────────────────────────────────────────────────────────────
    story.append(Paragraph("🚀 Key Features", style_h1))
    
    story.append(Paragraph("<b>• Dual-Language & Transliteration Pipeline:</b> Supports search queries in English and Hindi.", style_bullet))
    story.append(Paragraph("- Queries in Hindi are translated to English dynamically using Google Translate to fetch the most relevant rules.", style_bullet_2))
    story.append(Paragraph("- English responses from the LLM are translated back to Hindi (Devanagari script) using a local, CPU-optimized Indic translation model (sarvam-cpu).", style_bullet_2))
    story.append(Paragraph("- If Hinglish is detected, Devanagari Hindi is dynamically transliterated into conversational Roman script (Hinglish) at the end of the streaming pipeline.", style_bullet_2))
    
    story.append(Paragraph("<b>• Overlapped Pipelined Streaming:</b> Multi-threaded parallel translation loop. While a background thread streams English generation from the local LLM, the main thread translates completed sentences on-the-fly, reducing the user's perceived latency.", style_bullet))
    
    story.append(Paragraph("<b>• Conversational Memory:</b> Context-aware follow-ups. Short or vague follow-up queries (e.g. <i>\"next step kya hai?\"</i>) are semantically rewritten based on the recent conversation history to retrieve the correct contextual chunks.", style_bullet))
    
    story.append(Paragraph("<b>• Interactive PDF Viewer & Citations:</b> Every answer cites its source rules and document references (e.g. [Page 42]). Clicking the citation chip opens the PDF exactly on the cited page with the matched terms highlighted.", style_bullet))
    
    story.append(Paragraph("<b>• Interactive UI Actions:</b>", style_bullet))
    story.append(Paragraph("- <b>Text-to-Speech (TTS):</b> Play answers out loud in Hindi or English.", style_bullet_2))
    story.append(Paragraph("- <b>Copy to Clipboard:</b> Copy plain-text answers with markdown stripped.", style_bullet_2))
    story.append(Paragraph("- <b>Muted Footnote Disclaimer:</b> Subtle footnote indicating that the response is AI-generated for reference only.", style_bullet_2))
    story.append(Spacer(1, 0.2*cm))

    # ── Architecture ────────────────────────────────────────────────────────────
    story.append(Paragraph("🛠️ Architecture", style_h1))
    
    arch_data = [
        ["Module / Component", "Technology / Model"],
        ["Backend", "FastAPI (Python 3.11)"],
        ["Frontend", "React + Webpack (interactive chat widget)"],
        ["Vector Store", "Qdrant Database (separate collections: vendor_manuals & govt_rules)"],
        ["LLM Engine", "Fine-tuned Llama 3 8B / Qwen-2.5-3B (running locally via Ollama)"],
        ["Translation Model", "sarvam-cpu (Indic machine translation, running locally via Ollama)"],
        ["Embeddings Model", "bge-m3 / nomic-embed-text (running locally via Ollama)"],
    ]
    tbl = Table(arch_data, colWidths=[7*cm, 9*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9.5),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f6f8fa"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN",       (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ── Project Setup ───────────────────────────────────────────────────────────
    story.append(Paragraph("⚙️ Project Setup", style_h1))
    
    story.append(Paragraph("1. Prerequisites", style_h2))
    story.append(Paragraph("Ensure you have the following installed on your machine:", style_body))
    story.append(Paragraph("• Python 3.11", style_bullet))
    story.append(Paragraph("• Node.js (v18+)", style_bullet))
    story.append(Paragraph("• Ollama", style_bullet))
    
    story.append(Paragraph("2. Ollama Models", style_h2))
    story.append(Paragraph("Download the required models in Ollama before starting:", style_body))
    model_cmds = (
        "ollama pull mistral:latest\n"
        "ollama pull qwen2.5:3b\n"
        "ollama pull nomic-embed-text:latest\n"
        "# For Hindi translation:\n"
        "ollama pull mashriram/sarvam-1:latest"
    )
    story.append(Paragraph(model_cmds.replace("\n", "<br/>"), style_code))
    
    story.append(Paragraph("3. Backend Setup", style_h2))
    story.append(Paragraph("Navigate to the root directory and create a Python virtual environment:", style_body))
    backend_cmds = (
        "python -m venv venv\n"
        "source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
    )
    story.append(Paragraph(backend_cmds.replace("\n", "<br/>"), style_code))
    
    story.append(Paragraph("Install dependencies:", style_body))
    story.append(Paragraph("pip install -r requirements.txt", style_code))
    
    story.append(Paragraph("Run the document ingestion script to parse PDFs and populate the Vector Store:", style_body))
    story.append(Paragraph("venv\\Scripts\\python.exe scripts/ingest_documents.py", style_code))
    
    story.append(Paragraph("Start the FastAPI backend server:", style_body))
    story.append(Paragraph("venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000", style_code))
    
    story.append(Paragraph("4. Frontend Setup", style_h2))
    story.append(Paragraph("Navigate to the frontend folder, install packages, and launch development build:", style_body))
    frontend_cmds = (
        "cd frontend\n"
        "npm install\n"
        "npm run dev"
    )
    story.append(Paragraph(frontend_cmds.replace("\n", "<br/>"), style_code))
    story.append(Spacer(1, 0.2*cm))

    # ── Evaluation & Testing ────────────────────────────────────────────────────
    story.append(Paragraph("📊 Evaluation & Testing", style_h1))
    story.append(Paragraph("The repository contains automated testing suites to evaluate retrieval and response accuracy:", style_body))
    
    story.append(Paragraph("<b>• Retrieval Recall Test:</b> Evaluates Top-1, 3, 5, and 10 retrieval recall across 100 benchmark queries targeting complex PDFs.", style_bullet))
    story.append(Paragraph("python scripts/evaluate_rag.py", style_code))
    
    story.append(Paragraph("<b>• End-to-End KPI Test:</b> Uses LLM-as-a-judge to grade chatbot accuracy against a set of 80 ground-truth Q&As.", style_bullet))
    story.append(Paragraph("python scripts/run_kpi_testing.py", style_code))

    doc.build(story)
    print("README PDF generated successfully.")

if __name__ == "__main__":
    main()
