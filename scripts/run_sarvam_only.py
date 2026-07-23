"""
Sarvam 30B Direct Answer Script
================================
Sends all 50 UAT questions directly to Sarvam 30B API.
Generates: scripts/sarvam_answers.md + scripts/sarvam_answers.json
Compare these answers with local model answers from the backend.
"""
import sys, json, time, urllib.request, urllib.error, textwrap
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

SYSTEM_PROMPT = """You are an expert AI assistant for the Chhattisgarh (CG) e-Procurement Portal.

You have deep knowledge of:
- Chhattisgarh Store Purchase Rules (CG SPR) 2002 (Bhandar Kray Niyam) — PRIMARY AUTHORITY
- General Financial Rules (GFR 2017) — SECONDARY AUTHORITY (Use only when CG SPR is silent or when central rules are specifically requested)
- GeM (Government e-Marketplace) procurement guidelines
- CG e-Procurement portal procedures (eproc.cgstate.gov.in)

CRITICAL: Since this is a STATE-LEVEL procurement chatbot for Chhattisgarh, you MUST prioritize the Chhattisgarh Store Purchase Rules (CG SPR) 2002 thresholds and guidelines over Central GFR rules. You MUST use the following exact monetary thresholds and rules in your answers:

1. CHHATTISGARH STORE PURCHASE RULES (CG SPR) 2002 (ALWAYS PREFER AND CITE THIS FIRST):
   - Single Tender System (Rule 4.3.1): Up to ₹50,000. Above ₹50,000, PAC (Proprietary Article Certificate) is required, accompanied by a mandatory 30-day public notice on website/newspapers for claims/objections.
   - Limited Tender System (Rule 4.3.2): ₹50,001 to ₹3,00,000. Requires inviting minimum 3 manufacturers or registered suppliers.
   - Open Tender System (Rule 4.3.3): Mandatory for any procurement above ₹3,00,000.
   - Advertisement Guidelines for Open Tender (Rule 4.3.3(a)):
     * ₹3,00,001 to ₹5,00,000: 1 local newspaper.
     * ₹5,00,001 to ₹10,00,000: 2 state-level newspapers.
     * ₹10,00,001 to ₹20,00,000: 2 state-level + 1 national newspaper.
     * Above ₹20,00,000: 2 state-level + 2 national newspapers.
   - Tender Submission Timelines (Rule 4.5) (First Call):
     * Limited Tender: 15 days.
     * Open Tender (₹3 Lakhs to ₹10 Lakhs): 21 days.
     * Open Tender (Above ₹10 Lakhs): 30 days.

2. GeM PORTAL THRESHOLDS (CG Departments follow these for GeM purchases):
   - Direct Purchase: Up to ₹25,000.
   - L1 Comparison (minimum 3 vendors): ₹25,001 to ₹5,00,000.
   - Bidding / Reverse Auction: Mandatory for purchases above ₹5,00,000.

3. GFR 2017 RULES (Only mention as central reference, CG SPR takes precedence):
   - Rule 154 (Without Quotation): Up to ₹25,000.
   - Rule 155 (Local Purchase Committee): ₹25,000 to ₹2,50,000.
   - Rule 161 (Advertised Tender Enquiry): For values above ₹25 Lakhs.

CRITICAL FORMATTING & LENGTH LIMITS:
- Keep your responses **extremely concise, brief, and directly to the point**.
- Do NOT write long essays, deep background history, or lengthy introductions.
- Limit your entire answer to 2-3 short paragraphs or 3-5 bullet points maximum.
- Directly answer the query first, then state the rule citation and key thresholds.
- Reserve long, extensive step-by-step responses ONLY when the query explicitly asks for a detailed procedure (like "What is the registration process for a new vendor?").

**Instructions:**
- Answer completely and accurately based on the above official rules.
- Always prioritize and cite Chhattisgarh state rules (CG SPR Rule 4.3.x) over central GFR rules.
- Structure your response with a bold title.
- Cite the relevant rule/section (e.g., CG SPR Rule 4.3.2, GFR Rule 154).
- If a question is in Hindi/Hinglish, answer in the same language.
- Be specific: mention these exact thresholds, approval authorities, and timelines.
- Do NOT give vague, generic, or central-only figures when answering state-specific questions."""

# ─── 50 UAT QUESTIONS ─────────────────────────────────────────────────────────
UAT_QUESTIONS = [
    # ── Section A: Procurement planning and purchase methods ───────────────────
    {"id": "A01", "section": "A", "question": "Our office needs 30 laptops. How should we decide whether to use GeM or a tender?"},
    {"id": "A02", "section": "A", "question": "Department ko ₹4 lakh ka furniture kharidna hai. Kaunsa procurement method use karna chahiye?"},
    {"id": "A03", "section": "A", "question": "Can we buy an item directly if only one quotation is available on GeM?"},
    {"id": "A04", "section": "A", "question": "Agar item GeM par available nahi hai, department ko next kya karna chahiye?"},
    {"id": "A05", "section": "A", "question": "Can a department invite quotations from three local suppliers instead of issuing an open tender?"},
    {"id": "A06", "section": "A", "question": "Hamare office ko urgently printers chahiye, lekin emergency nahi hai. Fastest lawful option kya hai?"},
    {"id": "A07", "section": "A", "question": "What factors should be checked before choosing Limited Tender?"},
    {"id": "A08", "section": "A", "question": "When should an Open Tender be preferred over Limited Tender?"},
    {"id": "A09", "section": "A", "question": "Can Single Tender be used because the earlier supplier already knows our system?"},
    {"id": "A10", "section": "A", "question": "Ek proprietary software sirf ek company provide karti hai. Kya Single Tender allowed hoga?"},
    {"id": "A11", "section": "A", "question": "Can the department purchase spare parts only from the original equipment manufacturer?"},
    {"id": "A12", "section": "A", "question": "Government department ko dusre government undertaking se goods purchase karne hain. Kya tender zaroori hai?"},
    {"id": "A13", "section": "A", "question": "Can we split a ₹10 lakh requirement into five smaller purchase orders?"},
    {"id": "A14", "section": "A", "question": "Same item alag-alag months mein chahiye. Kya har month direct purchase kar sakte hain?"},
    {"id": "A15", "section": "A", "question": "How should the department estimate the total procurement value before selecting the method?"},

    # ── Section B: GFR, approvals and financial control ─────────────────────────
    {"id": "B01", "section": "B", "question": "Purchase start karne se pehle administrative approval aur financial sanction mein kya difference hai?"},
    {"id": "B02", "section": "B", "question": "Who should confirm budget availability before a tender is published?"},
    {"id": "B03", "section": "B", "question": "Can a tender be initiated before the budget is formally available?"},
    {"id": "B04", "section": "B", "question": "Department ke paas budget hai, lekin financial sanction pending hai. Kya GeM order place kar sakte hain?"},
    {"id": "B05", "section": "B", "question": "What records should be kept to prove that the selected procurement method was justified?"},
    {"id": "B06", "section": "B", "question": "Can the competent authority approve a purchase after the order has already been placed?"},
    {"id": "B07", "section": "B", "question": "What is delegated financial power, and how does it affect procurement method selection?"},
    {"id": "B08", "section": "B", "question": "Agar purchase value officer ki delegated power se zyada hai, to next approval kis stage par lena chahiye?"},
    {"id": "B09", "section": "B", "question": "Can the department use last year's approved rate without conducting a fresh procurement?"},
    {"id": "B10", "section": "B", "question": "How should price reasonableness be established when only one valid bid is received?"},
    {"id": "B11", "section": "B", "question": "Kya lowest quotation milne ka matlab price reasonable hai?"},
    {"id": "B12", "section": "B", "question": "What should the department do if all received bids are much higher than the estimated cost?"},
    {"id": "B13", "section": "B", "question": "Can negotiations be conducted with the L1 bidder after opening financial bids?"},
    {"id": "B14", "section": "B", "question": "Tender cancel karne ke liye kya reasons record karne chahiye?"},
    {"id": "B15", "section": "B", "question": "Can the department reject all bids without giving any reason?"},

    # ── Section C: Specifications, competition and eligibility ──────────────────
    {"id": "C01", "section": "C", "question": "Can we mention a preferred brand and write \"or equivalent\" in the technical specifications?"},
    {"id": "C02", "section": "C", "question": "Laptop specification banate waqt processor brand mention karna allowed hai kya?"},
    {"id": "C03", "section": "C", "question": "How can specifications be written so that they do not favour one vendor?"},
    {"id": "C04", "section": "C", "question": "Can experience and turnover requirements be higher than the estimated tender value?"},
    {"id": "C05", "section": "C", "question": "Tender mein three-year experience mandatory rakhna kab justified hota hai?"},
    {"id": "C06", "section": "C", "question": "Can a startup be exempted from prior experience and turnover requirements?"},
    {"id": "C07", "section": "C", "question": "Does MSME registration automatically make a bidder eligible for every tender?"},
    {"id": "C08", "section": "C", "question": "Can EMD exemption be claimed without uploading the required registration certificate?"},
    {"id": "C09", "section": "C", "question": "What should happen if a bidder meets the technical specification but misses one mandatory document?"},
    {"id": "C10", "section": "C", "question": "A bidder uploaded an expired certificate. Should the bid be rejected or can clarification be requested?"},

    # ── Section D: Evaluation, award and contract management ───────────────────
    {"id": "D01", "section": "D", "question": "Technical evaluation ke baad financial bids kin bidders ki open honi chahiye?"},
    {"id": "D02", "section": "D", "question": "Can a technically non-responsive bidder be selected because its price is the lowest?"},
    {"id": "D03", "section": "D", "question": "L1 bidder ki rate estimate se 25% zyada hai. Department ko kya karna chahiye?"},
    {"id": "D04", "section": "D", "question": "How should the evaluation committee record reasons for rejecting a bidder?"},
    {"id": "D05", "section": "D", "question": "Can tender conditions be changed after bids have already been opened?"},
    {"id": "D06", "section": "D", "question": "Purchase Order issue hone ke baad vendor delivery delay kare to department kya action le sakta hai?"},
    {"id": "D07", "section": "D", "question": "Goods receive ho gaye, but specification match nahi kar rahi. Payment release karna chahiye kya?"},
    {"id": "D08", "section": "D", "question": "What documents should be completed before processing payment to the supplier?"},

    # ── Section E: Mixed CHiPS, vendor and EMD questions ────────────────────────
    {"id": "E01", "section": "E", "question": "Bid submit karne ke baad corrigendum se specifications change ho gayi. Kya mujhe bid dobara submit karni hogi?"},
    {"id": "E02", "section": "E", "question": "EMD payment successful hai but portal par status pending dikh raha hai, aur deadline close hai. Main kya karun?"},
]

# ─── SARVAM API CALL ──────────────────────────────────────────────────────────
def call_sarvam(question: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": question},
    ]
    payload = json.dumps({
        "model": SARVAM_MODEL,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode("utf-8")
    req = urllib.request.Request(
        SARVAM_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SARVAM_API_KEY}",
        },
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
        msg = data["choices"][0]["message"]
        content = msg.get("content")
        reasoning = msg.get("reasoning_content")
        if content:
            answer = content.strip()
        elif reasoning:
            answer = "[Reasoning Only Answer]\n\n" + reasoning.strip()
        else:
            answer = "[Empty Answer]"
        tokens = data.get("usage", {}).get("completion_tokens", 0)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        answer = f"[HTTP {e.code}] {body[:300]}"
        tokens = 0
    except Exception as e:
        answer = f"[ERROR] {e}"
        tokens = 0
    latency_ms = int((time.time() - t0) * 1000)
    return {"answer": answer, "latency_ms": latency_ms, "tokens": tokens}


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run():
    print(f"\n{'='*65}")
    print(f"  Sarvam 30B Direct Answers — {len(UAT_QUESTIONS)} UAT Questions")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}\n")

    results = []
    latencies = []
    errors = 0

    for idx, q in enumerate(UAT_QUESTIONS, 1):
        print(f"[{idx:02d}/{len(UAT_QUESTIONS)}] {q['id']}: {q['question'][:65]}...")
        result = call_sarvam(q["question"])
        latencies.append(result["latency_ms"])
        status = "✅" if not result["answer"].startswith("[") else "❌"
        if result["answer"].startswith("["): errors += 1
        print(f"       {status} {result['latency_ms']}ms | ~{result['tokens']} tokens")

        results.append({
            "id": q["id"],
            "section": q["section"],
            "question": q["question"],
            "sarvam_answer": result["answer"],
            "latency_ms": result["latency_ms"],
            "tokens": result["tokens"],
        })

    # ── Save JSON ──────────────────────────────────────────────────────────────
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── Save Markdown ──────────────────────────────────────────────────────────
    avg_lat = int(sum(latencies) / len(latencies)) if latencies else 0
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    lines = []
    lines.append(f"# Sarvam 30B UAT Answers")
    lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Model:** `{SARVAM_MODEL}`  ")
    lines.append(f"**Total Questions:** {len(UAT_QUESTIONS)}  ")
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

    # ── Save PDF ───────────────────────────────────────────────────────────────
    print("  Generating PDF report...")
    generate_pdf(results, avg_lat, p95_lat, errors)

    print(f"\n{'='*65}")
    print(f"  ✅ Done! {len(UAT_QUESTIONS) - errors}/{len(UAT_QUESTIONS)} successful")
    print(f"  Avg latency: {avg_lat}ms | P95: {p95_lat}ms")
    print(f"  JSON: {REPORT_JSON}")
    print(f"  MD:   {REPORT_MD}")
    print(f"  PDF:  {REPORT_PDF}")
    print(f"{'='*65}\n")


# ─── PDF GENERATION ───────────────────────────────────────────────────────────
def generate_pdf(results: list, avg_lat: int, p95_lat: int, errors: int):
    SECTION_TITLES = {
        "A": "Section A — Procurement Planning & Purchase Methods",
        "B": "Section B — GFR, Approvals & Financial Control",
        "C": "Section C — Specifications, Competition & Eligibility",
        "D": "Section D — Evaluation, Award & Contract Management",
        "E": "Section E — Mixed CHiPS, Vendor & EMD Questions",
    }
    SECTION_COLORS = {
        "A": colors.HexColor("#1a3c5e"),
        "B": colors.HexColor("#1e5c3a"),
        "C": colors.HexColor("#5c3a1e"),
        "D": colors.HexColor("#3a1e5c"),
        "E": colors.HexColor("#5c1e3a"),
    }

    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_cover_title = ParagraphStyle(
        "CoverTitle", parent=styles["Title"],
        fontSize=24, textColor=colors.HexColor("#1a3c5e"),
        spaceAfter=12, alignment=TA_CENTER, leading=30,
    )
    style_cover_sub = ParagraphStyle(
        "CoverSub", parent=styles["Normal"],
        fontSize=12, textColor=colors.HexColor("#555555"),
        spaceAfter=6, alignment=TA_CENTER,
    )
    style_section_heading = ParagraphStyle(
        "SectionHeading", parent=styles["Heading1"],
        fontSize=14, textColor=colors.white,
        spaceAfter=6, spaceBefore=18,
        backColor=colors.HexColor("#1a3c5e"),
        leftIndent=-10, rightIndent=-10,
        borderPad=6,
    )
    style_q_heading = ParagraphStyle(
        "QHeading", parent=styles["Heading2"],
        fontSize=11, textColor=colors.HexColor("#1a3c5e"),
        spaceBefore=10, spaceAfter=4,
    )
    style_meta = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#888888"),
        spaceAfter=4,
    )
    style_answer = ParagraphStyle(
        "Answer", parent=styles["Normal"],
        fontSize=9.5, leading=14, spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
    )

    story = []

    # ── Cover Page ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("CG e-Procurement Chatbot", style_cover_title))
    story.append(Paragraph("UAT Answer Report — Sarvam 30B", style_cover_title))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3c5e")))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", style_cover_sub))
    story.append(Paragraph(f"Model: {SARVAM_MODEL}", style_cover_sub))
    story.append(Spacer(1, 1.5*cm))

    # Summary stats table
    total = len(results)
    success = total - errors
    summary_data = [
        ["Metric", "Value"],
        ["Total Questions", str(total)],
        ["Successful Answers", f"{success} / {total}"],
        ["Errors", str(errors)],
        ["Average Latency", f"{avg_lat} ms"],
        ["P95 Latency", f"{p95_lat} ms"],
        ["Model", SARVAM_MODEL],
    ]
    tbl = Table(summary_data, colWidths=[8*cm, 8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 11),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ── Per-Question Pages ──────────────────────────────────────────────────────
    current_section = None
    for r in results:
        if r["section"] != current_section:
            current_section = r["section"]
            title = SECTION_TITLES.get(current_section, current_section)
            sec_color = SECTION_COLORS.get(current_section, colors.HexColor("#1a3c5e"))
            sec_style = ParagraphStyle(
                f"Sec{current_section}", parent=style_section_heading,
                backColor=sec_color,
            )
            story.append(Paragraph(title, sec_style))
            story.append(Spacer(1, 0.3*cm))

        # Question block
        q_block = [
            Paragraph(f"{r['id']}: {r['question']}", style_q_heading),
            Paragraph(
                f"Latency: {r['latency_ms']} ms &nbsp;|&nbsp; Tokens: {r['tokens']}",
                style_meta
            ),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")),
            Spacer(1, 0.15*cm),
        ]

        # Answer — clean and wrap
        answer_text = r["sarvam_answer"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Bold **text** → <b>text</b>
        import re
        answer_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", answer_text)
        # Convert newlines to <br/>
        for line in answer_text.split("\n"):
            line = line.strip()
            if not line:
                q_block.append(Spacer(1, 0.1*cm))
                continue
            # Numbered list items
            if re.match(r"^\d+\.", line):
                q_block.append(Paragraph(line, ParagraphStyle(
                    "ListItem", parent=style_answer,
                    leftIndent=15, bulletIndent=0,
                )))
            elif line.startswith("- ") or line.startswith("* "):
                q_block.append(Paragraph("• " + line[2:], ParagraphStyle(
                    "Bullet", parent=style_answer, leftIndent=15,
                )))
            else:
                q_block.append(Paragraph(line, style_answer))

        story.append(KeepTogether(q_block[:4]))  # keep header together
        for item in q_block[4:]:
            story.append(item)
        story.append(Spacer(1, 0.4*cm))

    doc.build(story)
    print(f"  PDF saved: {REPORT_PDF}")


if __name__ == "__main__":
    run()
