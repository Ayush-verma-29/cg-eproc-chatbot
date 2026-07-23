# scripts/run_dual_evaluation.py
import os
import sys
import json
import time
import urllib.request
import urllib.error
import re
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
BASE_URL       = "http://localhost:8001"
SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_API_KEY = "sk_wnn7d9p5_Wwo3KdUINlvAYW0GkKEh4WRv"
SARVAM_MODEL   = "sarvam-30b"

REPORT_JSON    = Path(__file__).parent / "dual_evaluation_report.json"
REPORT_MD      = Path(__file__).parent / "dual_evaluation_report.md"
REPORT_PDF     = Path(__file__).parent / "dual_evaluation_report.pdf"

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

# ─── 50 NEW UAT QUESTIONS ─────────────────────────────────────────────────────
NEW_UAT_QUESTIONS = [
    # Category A: Store Purchase Rules & Procurement Planning
    {"id": "A01", "section": "A", "actor": "government_officer", "question": "Office ko ₹50,000 ka printer cartridge purchase karna hai. Chhattisgarh Store Purchase Rules ke under direct purchase allowed hai kya?"},
    {"id": "A02", "section": "A", "actor": "government_officer", "question": "What is the maximum duration for which a short-term tender notice of 2 days can be issued under CG procurement regulations?"},
    {"id": "A03", "section": "A", "actor": "government_officer", "question": "क्या छत्तीसगढ़ भंडार क्रय नियमों के अंतर्गत स्थानीय उद्योगों (Local MSEs) को मूल्य वरीयता (Price Preference) का लाभ मिलता है?"},
    {"id": "A04", "section": "A", "actor": "government_officer", "question": "Under what circumstances can a department issue a limited tender without publishing a Notice Inviting Tender (NIT) in local newspapers?"},
    {"id": "A05", "section": "A", "actor": "government_officer", "question": "Hume ₹15 lakh ka networking project initiate karna hai, isme Limited Tender works rule apply hoga ya Goods procurement rule?"},
    {"id": "A06", "section": "A", "actor": "government_officer", "question": "क्या भंडार क्रय नियमों के अनुसार तकनीकी रूप से अयोग्य निविदाकर्ता की वित्तीय निविदा खोली जा सकती है?"},
    {"id": "A07", "section": "A", "actor": "government_officer", "question": "Can a department purchase items from a cooperative society or public sector undertaking directly, and is there any value limit under CG rules?"},
    {"id": "A08", "section": "A", "actor": "government_officer", "question": "Humare office ko aane wale financial year ke liye annual maintenance services plan karni hai. Estimated budget kaise calculate karein?"},
    {"id": "A09", "section": "A", "actor": "government_officer", "question": "क्या आपातकालीन चिकित्सा उपकरणों की खरीद के लिए भी भंडार क्रय नियम (Store Purchase Rules) के तहत खुली निविदा आवश्यक है?"},
    {"id": "A10", "section": "A", "actor": "government_officer", "question": "Is there a specific threshold value in Chhattisgarh Store Purchase Rules above which procurement through the state e-procurement portal becomes mandatory?"},

    # Category B: GFR, Financial Sanctions & CVC Vigilance Guidelines
    {"id": "B01", "section": "B", "actor": "government_officer", "question": "GFR Rule 144(xi) restricts bidders from countries sharing land borders with India. Does this apply to state-level sub-contracts as well?"},
    {"id": "B02", "section": "B", "actor": "government_officer", "question": "Humare project ka administrative approval toh mil gaya hai, par actual purchase se pehle final financial sanction kis authority se leni chahiye?"},
    {"id": "B03", "section": "B", "actor": "government_officer", "question": "क्या निविदा खुलने के बाद बोली लगाने वालों के बीच दरें (rates) बदलने के लिए कार्टेल (Cartelization) की जांच सीवीसी द्वारा की जाती है?"},
    {"id": "B04", "section": "B", "actor": "government_officer", "question": "Under what GFR rule can a Proprietary Article Certificate (PAC) be signed, and what is its validity period?"},
    {"id": "B05", "section": "B", "actor": "government_officer", "question": "Agar emergency me COVID test kits kharidne padein bina competitive bidding ke, to kis GFR rule ke under justify karna hoga?"},
    {"id": "B06", "section": "B", "actor": "government_officer", "question": "क्या बिना प्रशासनिक स्वीकृति (Administrative Approval) के निविदा प्रक्रिया (tender process) प्रारंभ की जा सकती है?"},
    {"id": "B07", "section": "B", "actor": "government_officer", "question": "What are the CVC guidelines on the validity and extension of bank guarantees submitted as performance security?"},
    {"id": "B08", "section": "B", "actor": "government_officer", "question": "Single tender invite karne par agar sirf wahi purana vendor response kare, to kya uski rate direct accept kar sakte hain?"},
    {"id": "B09", "section": "B", "actor": "government_officer", "question": "सीवीसी (CVC) निर्देशों के अनुसार निविदा में 'Negotiations' (वार्ता) केवल न्यूनतम बोलीदाता (L1) के साथ ही क्यों की जा सकती है?"},
    {"id": "B10", "section": "B", "actor": "government_officer", "question": "Does GFR allow purchase of goods through a search on GeM using the \"Custom Bid\" feature when standard specifications do not match?"},

    # Category C: Specifications, Bidder Eligibility & MSME Exemptions
    {"id": "C01", "section": "C", "actor": "government_officer", "question": "Specs me \"high-quality RAM\" ya \"fast processor\" jaise ambiguous terms use karne par CVC guidelines kya kehti hain?"},
    {"id": "C02", "section": "C", "actor": "government_officer", "question": "क्या किसी निविदा में निविदाकर्ताओं के लिए न्यूनतम वार्षिक टर्नओवर (Minimum Annual Turnover) का मानदंड रखना अनिवार्य है?"},
    {"id": "C03", "section": "C", "actor": "government_officer", "question": "Can we require the bidder to have a local service center in Chhattisgarh to qualify for the technical evaluation?"},
    {"id": "C04", "section": "C", "actor": "government_officer", "question": "MSME certificate hone par EMD exemption to mil jata hai, par kya performance security (SD) se bhi exemption milta hai?"},
    {"id": "C05", "section": "C", "actor": "government_officer", "question": "क्या निविदा शुरू होने के बाद किसी एक निविदाकर्ता के अनुरोध पर अर्हता शर्तों (eligibility criteria) को शिथिल किया जा सकता है?"},
    {"id": "C06", "section": "C", "actor": "government_officer", "question": "How should we handle a bid where the MSME certificate is valid but does not cover the specific category of items being procured?"},
    {"id": "C07", "section": "C", "actor": "government_officer", "question": "Technical bid sheet me bid capability verify karne ke liye kya past performance report accept karni chahiye?"},
    {"id": "C08", "section": "C", "actor": "government_officer", "question": "यदि बोलीदाता ने मूल दस्तावेज अपलोड नहीं किए हैं, केवल स्व-सत्यापित (self-attested) प्रतियां दी हैं, तो क्या बोली स्वीकार्य है?"},
    {"id": "C09", "section": "C", "actor": "government_officer", "question": "Under GFR rules, are startup entities registered with DPIIT exempted from the \"prior experience\" criteria if they meet quality specifications?"},
    {"id": "C10", "section": "C", "actor": "government_officer", "question": "Department laptop specification me screen resolution exact 1920x1080 px likh sakta hai ya ranges dena zaroori hai?"},

    # Category D: Bid Evaluation, Negotiations (L1) & Contract Award
    {"id": "D01", "section": "D", "actor": "government_officer", "question": "If the L1 bidder backs out after the financial evaluation, can we award the contract to the L2 bidder at L1 rates?"},
    {"id": "D02", "section": "D", "actor": "government_officer", "question": "Technical comparative statement verify karte waqt agar kisi point par contradiction ho, to evaluation committee kya step legi?"},
    {"id": "D03", "section": "D", "actor": "government_officer", "question": "क्या बोलीदाता को तकनीकी मूल्यांकन (Technical Evaluation) में असफल होने का कारण बताना विभाग के लिए अनिवार्य है?"},
    {"id": "D04", "section": "D", "actor": "government_officer", "question": "What is the process to be followed if the lowest bid (L1) is received from a joint venture or consortium instead of an individual firm?"},
    {"id": "D05", "section": "D", "actor": "government_officer", "question": "Final award se pehle agar department ko pata chale ki L1 bidder ne fake experience certificate submit kiya hai, to kya action lena hoga?"},
    {"id": "D06", "section": "D", "actor": "government_officer", "question": "क्या वित्तीय बोलियां (Financial Bids) खोलने के तुरंत बाद कार्य आदेश (Work Order) जारी किया जा सकता है?"},
    {"id": "D07", "section": "D", "actor": "government_officer", "question": "Under what circumstances can a purchase order be amended after it has been signed by both parties?"},
    {"id": "D08", "section": "D", "actor": "government_officer", "question": "Agar multiple bidders ke quotes exact same ho (Tied L1), to tender award karne ke liye tie-breaker rule kya hai?"},
    {"id": "D09", "section": "D", "actor": "government_officer", "question": "क्या बोलीदाता द्वारा जमा की गई बैंक गारंटी (Performance Security) को अनुबंध के उल्लंघन पर जब्त (forfeit) किया जा सकता है?"},
    {"id": "D10", "section": "D", "actor": "government_officer", "question": "What is the maximum percentage of delivery delay penalty (liquidated damages) that can be levied on a defaulting vendor under standard contracts?"},

    # Category E: Portal Operations, DSC & Technical Troubleshooting
    {"id": "E01", "section": "E", "actor": "vendor", "question": "New vendor registration ke time portal par DSC registration verify karte waqt 'Java error' aaye to browser settings me kya changes karein?"},
    {"id": "E02", "section": "E", "actor": "vendor", "question": "क्या बोलीदाता निविदा जमा करने की अंतिम तिथि समाप्त होने के बाद भी अपने दस्तावेज़ संशोधित कर सकता है?"},
    {"id": "E03", "section": "E", "actor": "vendor", "question": "How long does the portal take to automatically initiate the online EMD refund for bidders who are rejected at the technical round?"},
    {"id": "E04", "section": "E", "actor": "vendor", "question": "Portal par bid decrypt karne ke liye technical opener ko personal Class-III DSC check karna kyun mandatory hota hai?"},
    {"id": "E05", "section": "E", "actor": "vendor", "question": "क्या शुद्धिपत्र (Corrigendum) जारी करने पर निविदा जमा करने की अंतिम तिथि को बढ़ाना अनिवार्य है?"},
    {"id": "E06", "section": "E", "actor": "vendor", "question": "If the online payment gateway fails during the payment of tender document fees, how can the bidder retrieve the transaction receipt?"},
    {"id": "E07", "section": "E", "actor": "vendor", "question": "Edge browser setup guide ke according dynamic links open karne ke liye 'IE Mode' active hona kyun required hai?"},
    {"id": "E08", "section": "E", "actor": "vendor", "question": "क्या टेंडर ऑपरेटर तकनीकी बोली खोलने (Technical Bid Opening) के लिए स्वयं उत्तरदायी है या इसमें अप्रूवर की सहमति भी चाहिए?"},
    {"id": "E09", "section": "E", "actor": "vendor", "question": "What is the procedure on the CHiPS e-procurement portal if a bidder wants to submit EMD via NEFT/RTGS challan instead of net banking?"},
    {"id": "E10", "section": "E", "actor": "vendor", "question": "Portal par commercial schedule (BOQ.xls) fill karte waqt formula modification error aaye to vendor ko kya karna chahiye?"},
]

# ─── API HELPERS ───────────────────────────────────────────────────────────────

def start_session(role: str) -> str:
    """Initialize a session with the local backend API."""
    payload = json.dumps({"role": role}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/start",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["session_id"]
    except Exception as e:
        print(f"Error starting local session for role {role}: {e}")
        return ""

def send_local_chat(question: str, session_id: str) -> dict:
    """Send request to local chatbot and stream response."""
    payload = json.dumps({"question": question, "session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    accumulated = ""
    sources = []
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].strip())
                    etype = event.get("type", "")
                    if etype == "token":
                        accumulated += event.get("text", "")
                    elif etype == "replace":
                        accumulated = event.get("text", "")
                    elif etype == "sources":
                        sources = event.get("sources", [])
                    elif etype == "done":
                        break
                except Exception:
                    pass
    except urllib.error.HTTPError as e:
        accumulated = f"[HTTP {e.code}] {e.reason}"
    except Exception as e:
        accumulated = f"[ERROR] {e}"
    
    latency_ms = int((time.time() - t0) * 1000)
    return {
        "answer": accumulated.strip(),
        "sources": sources,
        "latency_ms": latency_ms
    }

def call_sarvam(question: str) -> dict:
    """Call Sarvam 30B API."""
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

def run_evaluation():
    print(f"\n{'='*75}")
    print(f"  CG e-Procurement Chatbot - Dual Model Evaluation (50 Questions)")
    print(f"  Local Model (Ollama) VS. Sarvam 30B Model")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*75}\n")
    
    # Initialize local sessions
    sessions = {
        "government_officer": start_session("government_officer"),
        "vendor": start_session("vendor")
    }
    print(f"Local sessions created: officer={sessions['government_officer'][:8]}... vendor={sessions['vendor'][:8]}...\n")
    
    results = []
    local_latencies = []
    sarvam_latencies = []
    
    for idx, q in enumerate(NEW_UAT_QUESTIONS, 1):
        print(f"[{idx:02d}/50] Running {q['id']}: {q['question'][:60]}...")
        
        # 1. Local Model Call
        session_id = sessions[q["actor"]]
        local_res = send_local_chat(q["question"], session_id)
        # Check session expiry / retry
        if "[HTTP 401]" in local_res["answer"] or "[ERROR] HTTP Error 401" in local_res["answer"]:
            print(f"       Local Session expired, restarting...")
            sessions[q["actor"]] = start_session(q["actor"])
            session_id = sessions[q["actor"]]
            local_res = send_local_chat(q["question"], session_id)
            
        local_latencies.append(local_res["latency_ms"])
        print(f"       -> Local Model:  {local_res['latency_ms']}ms | Sources: {len(local_res['sources'])} cited")
        
        # 2. Sarvam Model Call
        sarvam_res = call_sarvam(q["question"])
        sarvam_latencies.append(sarvam_res["latency_ms"])
        print(f"       -> Sarvam 30B:  {sarvam_res['latency_ms']}ms | Tokens: {sarvam_res['tokens']}")
        
        results.append({
            "id": q["id"],
            "section": q["section"],
            "actor": q["actor"],
            "question": q["question"],
            "local_answer": local_res["answer"],
            "local_sources": local_res["sources"],
            "local_latency_ms": local_res["latency_ms"],
            "sarvam_answer": sarvam_res["answer"],
            "sarvam_latency_ms": sarvam_res["latency_ms"],
            "sarvam_tokens": sarvam_res["tokens"]
        })
        
        # Cool-down to prevent rate-limiting/overload
        time.sleep(0.5)

    # ─── SAVE JSON ──────────────────────────────────────────────────────────────
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved raw results to: {REPORT_JSON}")

    # ─── SAVE MARKDOWN ──────────────────────────────────────────────────────────
    generate_markdown_report(results, local_latencies, sarvam_latencies)
    print(f"Saved Markdown report to: {REPORT_MD}")

    # ─── SAVE PDF ───────────────────────────────────────────────────────────────
    generate_pdf_report(results, local_latencies, sarvam_latencies)
    print(f"Saved PDF report to: {REPORT_PDF}")
    
    print(f"\n{'='*75}")
    print(f"🎉 DUAL EVALUATION RUN COMPLETED SUCCESSFULLY!")
    print(f"{'='*75}\n")


def generate_markdown_report(results, local_lats, sarvam_lats):
    avg_local = int(sum(local_lats) / len(local_lats)) if local_lats else 0
    p95_local = sorted(local_lats)[int(len(local_lats) * 0.95)] if local_lats else 0
    
    avg_sarvam = int(sum(sarvam_lats) / len(sarvam_lats)) if sarvam_lats else 0
    p95_sarvam = sorted(sarvam_lats)[int(len(sarvam_lats) * 0.95)] if sarvam_lats else 0

    lines = []
    lines.append("# CG e-Procurement Chatbot - Dual Model Evaluation Report")
    lines.append(f"\n**Evaluation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Test Set size:** 50 Questions (Store & Purchase Rules scenario questions)  ")
    lines.append("\n## Model Configuration and Latency Summary\n")
    
    lines.append("| Model / Parameter | Avg Latency (ms) | P95 Latency (ms) | Model Identifier |")
    lines.append("|---|---|---|---|")
    lines.append(f"| **Local Model (Ollama)** | {avg_local}ms | {p95_local}ms | `cg-procurement-chatbot` |")
    lines.append(f"| **Sarvam 30B Model** | {avg_sarvam}ms | {p95_sarvam}ms | `sarvam-30b` |")
    
    lines.append("\n---\n")
    lines.append("## Detailed Per-Question Full Responses")
    
    sections = {
        "A": "Section A: Store Purchase Rules & Procurement Planning",
        "B": "Section B: GFR, Approvals & Financial Control",
        "C": "Section C: Specifications, Bidder Eligibility & MSME Exemptions",
        "D": "Section D: Bid Evaluation, Negotiations (L1) & Contract Award",
        "E": "Section E: Portal Operations, DSC & Technical Troubleshooting"
    }
    
    current_sec = None
    for r in results:
        if r["section"] != current_sec:
            current_sec = r["section"]
            lines.append(f"\n\n## {sections[current_sec]}\n")
            
        lines.append(f"\n### Question {r['id']}: {r['question']}")
        lines.append(f"**Expected Actor Role:** `{r['actor']}`\n")
        
        # Side-by-side or block compare
        lines.append("#### 💻 Local Model (Ollama)")
        lines.append(f"*Latency:* {r['local_latency_ms']} ms | *Retrieved Sources:* {', '.join(r['local_sources']) if r['local_sources'] else 'None Cited'}")
        lines.append("\n```text")
        lines.append(r["local_answer"])
        lines.append("```\n")
        
        lines.append("#### 🇮🇳 Sarvam 30B API")
        lines.append(f"*Latency:* {r['sarvam_latency_ms']} ms | *Completion Tokens:* {r['sarvam_tokens']}")
        lines.append("\n```text")
        lines.append(r["sarvam_answer"])
        lines.append("```\n")
        lines.append("---\n")
        
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_pdf_report(results, local_lats, sarvam_lats):
    avg_local = int(sum(local_lats) / len(local_lats)) if local_lats else 0
    p95_local = sorted(local_lats)[int(len(local_lats) * 0.95)] if local_lats else 0
    avg_sarvam = int(sum(sarvam_lats) / len(sarvam_lats)) if sarvam_lats else 0
    p95_sarvam = sorted(sarvam_lats)[int(len(sarvam_lats) * 0.95)] if sarvam_lats else 0

    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=2.0*cm, bottomMargin=2.0*cm,
    )
    
    styles = getSampleStyleSheet()
    
    style_cover_title = ParagraphStyle(
        "CoverTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1A3C5E"),
        spaceAfter=12, alignment=TA_CENTER, leading=26,
    )
    style_cover_sub = ParagraphStyle(
        "CoverSub", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#555555"),
        spaceAfter=6, alignment=TA_CENTER,
    )
    style_section_heading = ParagraphStyle(
        "SectionHeading", parent=styles["Heading1"],
        fontSize=13, textColor=colors.white,
        spaceAfter=6, spaceBefore=16,
        backColor=colors.HexColor("#1A3C5E"),
        leftIndent=-8, rightIndent=-8,
        borderPad=5,
    )
    style_q_heading = ParagraphStyle(
        "QHeading", parent=styles["Heading2"],
        fontSize=10, textColor=colors.HexColor("#1A3C5E"),
        spaceBefore=8, spaceAfter=4,
    )
    style_meta = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=7.5, textColor=colors.HexColor("#666666"),
        spaceAfter=3,
    )
    style_model_tag = ParagraphStyle(
        "ModelTag", parent=styles["Normal"],
        fontSize=8.5, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2B547E"),
        spaceBefore=4, spaceAfter=2,
    )
    style_answer = ParagraphStyle(
        "Answer", parent=styles["Normal"],
        fontSize=8.5, leading=11, spaceAfter=4,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
    )
    
    story = []
    
    # Title Cover Page
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("CG e-Procurement Chatbot Evaluation", style_cover_title))
    story.append(Paragraph("Dual Model Response & Performance Report", style_cover_title))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1A3C5E")))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", style_cover_sub))
    story.append(Spacer(1, 1.0*cm))
    
    summary_data = [
        ["Model Name", "Avg Latency", "P95 Latency", "Model Type"],
        ["Local Model (Ollama)", f"{avg_local} ms", f"{p95_local} ms", "Custom LLM w/ RAG"],
        ["Sarvam 30B Model", f"{avg_sarvam} ms", f"{p95_sarvam} ms", "API Chat Model"]
    ]
    tbl = Table(summary_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 4.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1A3C5E")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 10),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F0F4F8"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(PageBreak())
    
    # Per Question Section
    sections = {
        "A": "Section A: Store Purchase Rules & Procurement Planning",
        "B": "Section B: GFR, Approvals & Financial Control",
        "C": "Section C: Specifications, Bidder Eligibility & MSME Exemptions",
        "D": "Section D: Bid Evaluation, Negotiations (L1) & Contract Award",
        "E": "Section E: Portal Operations, DSC & Technical Troubleshooting"
    }
    
    current_sec = None
    for r in results:
        if r["section"] != current_sec:
            current_sec = r["section"]
            sec_title = sections.get(current_sec, current_sec)
            story.append(Paragraph(sec_title, style_section_heading))
            story.append(Spacer(1, 0.2*cm))
            
        q_block = []
        q_block.append(Paragraph(f"Question {r['id']}: {r['question']}", style_q_heading))
        q_block.append(Paragraph(f"Expected Actor Role: <b>{r['actor']}</b>", style_meta))
        q_block.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
        q_block.append(Spacer(1, 0.1*cm))
        
        # Local Answer
        q_block.append(Paragraph(f"💻 Local Model (Latency: {r['local_latency_ms']} ms | Sources: {len(r['local_sources'])}):", style_model_tag))
        local_text = r["local_answer"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        local_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", local_text)
        for line in local_text.split("\n"):
            line = line.strip()
            if not line:
                q_block.append(Spacer(1, 0.05*cm))
                continue
            q_block.append(Paragraph(line, style_answer))
            
        # Sarvam Answer
        q_block.append(Spacer(1, 0.1*cm))
        q_block.append(Paragraph(f"🇮🇳 Sarvam 30B Model (Latency: {r['sarvam_latency_ms']} ms | Tokens: {r['sarvam_tokens']}):", style_model_tag))
        sarvam_text = r["sarvam_answer"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        sarvam_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", sarvam_text)
        for line in sarvam_text.split("\n"):
            line = line.strip()
            if not line:
                q_block.append(Spacer(1, 0.05*cm))
                continue
            q_block.append(Paragraph(line, style_answer))
            
        q_block.append(Spacer(1, 0.2*cm))
        
        # Build KeepTogether block or push individually
        story.append(KeepTogether(q_block[:5]))
        for idx in range(5, len(q_block)):
            story.append(q_block[idx])
        story.append(Spacer(1, 0.3*cm))
        
    doc.build(story)


if __name__ == "__main__":
    run_evaluation()
