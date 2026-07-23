"""
Retry Failed UAT Questions
=========================
Loads sarvam_answers.json, finds questions with "[ERROR]" responses,
re-queries only those from the Sarvam API, updates the files, and
re-generates both MD and PDF.
"""
import sys, json, time, urllib.request, urllib.error, re
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

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_API_KEY = "sk_wnn7d9p5_Wwo3KdUINlvAYW0GkKEh4WRv"
SARVAM_MODEL   = "sarvam-30b"
REPORT_MD      = Path(__file__).parent / "sarvam_answers.md"
REPORT_JSON    = Path(__file__).parent / "sarvam_answers.json"
REPORT_PDF     = Path(__file__).parent / "sarvam_answers.pdf"

from run_sarvam_only import SYSTEM_PROMPT, call_sarvam, generate_pdf

def main():
    if not REPORT_JSON.exists():
        print("JSON report not found. Run run_sarvam_only.py first.")
        return
        
    print(f"Loading {REPORT_JSON}...")
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    failed = [r for r in results if r.get("sarvam_answer", "").startswith("[ERROR]")]
    if not failed:
        print("🎉 No failed questions found!")
        return
        
    print(f"Found {len(failed)} failed questions to retry: {[r['id'] for r in failed]}")
    
    for r in failed:
        print(f"Retrying {r['id']}: {r['question'][:65]}...")
        # Increase timeout or try multiple times if needed
        result = call_sarvam(r["question"])
        
        status = "✅" if not result["answer"].startswith("[") else "❌"
        print(f"       {status} {result['latency_ms']}ms | ~{result['tokens']} tokens")
        
        # Update the result dict
        r["sarvam_answer"] = result["answer"]
        r["latency_ms"] = result["latency_ms"]
        r["tokens"] = result["tokens"]
        
    # Save the updated JSON
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    # Recalculate stats
    latencies = [r["latency_ms"] for r in results]
    avg_lat = int(sum(latencies) / len(latencies))
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
    errors = sum(1 for r in results if r["sarvam_answer"].startswith("["))
    
    # ── Re-save MD ─────────────────────────────────────────────────────────────
    lines = []
    lines.append(f"# Sarvam 30B UAT Answers")
    lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Model:** `{SARVAM_MODEL}`  ")
    lines.append(f"**Total Questions:** {len(results)}  ")
    lines.append(f"**Errors:** {errors}  ")
    lines.append(f"**Avg Latency:** {avg_lat}ms | **P95 Latency:** {p95_lat}ms\n")
    lines.append("---\n")

    current_section = None
    SECTION_TITLES = {
        "A": "Section A — Procurement Planning & Purchase Methods",
        "B": "Section B — GFR, Approvals & Financial Control",
        "C": "Section C — Specifications, Competition & Eligibility",
        "D": "Section D — Evaluation, Award & Contract Management",
        "E": "Section E — Mixed CHiPS, Vendor & EMD Questions",
    }

    for r in results:
        if r["section"] != current_section:
            current_section = r["section"]
            lines.append(f"\n## {SECTION_TITLES.get(current_section, current_section)}\n")

        lines.append(f"---\n")
        lines.append(f"### {r['id']}: {r['question']}\n")
        lines.append(f"**Latency:** {r['latency_ms']}ms | **Tokens:** {r['tokens']}\n")
        lines.append(f"**Sarvam 30B Answer:**\n")
        lines.append(f"{r['sarvam_answer']}\n")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    # ── Re-generate PDF ────────────────────────────────────────────────────────
    print("Re-generating PDF...")
    generate_pdf(results, avg_lat, p95_lat, errors)
    print("🎉 Done! All failed questions retried and updated.")

if __name__ == "__main__":
    main()
