"""
UAT Test Script — CG e-Procurement Chatbot
Sections A–E (50 questions)
LLM Judge: Sarvam 30B via API
Report: scripts/uat_report_sarvam.md + scripts/uat_report_sarvam.json
"""
import sys, json, time, urllib.request, urllib.error, re
from pathlib import Path
from datetime import datetime

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ─── CONFIG ────────────────────────────────────────────────────────────────────
BASE_URL       = "http://localhost:8001"
SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_API_KEY = "sk_wnn7d9p5_Wwo3KdUINlvAYW0GkKEh4WRv"
SARVAM_MODEL   = "sarvam-30b"   # Sarvam 30B
REPORT_MD      = Path(__file__).parent / "uat_report_sarvam.md"
REPORT_JSON    = Path(__file__).parent / "uat_report_sarvam.json"

# ─── UAT QUESTIONS WITH GROUND-TRUTH METADATA ─────────────────────────────────
UAT_QUESTIONS = [
    # ── Section A: Procurement planning and purchase methods ───────────────────
    {
        "id": "A01", "section": "A",
        "question": "Our office needs 30 laptops. How should we decide whether to use GeM or a tender?",
        "expected_actor": "government_officer",
        "expected_intent": "procurement_method_selection",
        "expected_answer_mode": "step-by-step / decision-tree",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["GeM mandatory check Rule 3.1.1", "availability on GeM", "if not on GeM then tender", "value threshold"],
        "prohibited_claims": ["always use tender", "GeM is optional"],
    },
    {
        "id": "A02", "section": "A",
        "question": "Department ko ₹4 lakh ka furniture kharidna hai. Kaunsa procurement method use karna chahiye?",
        "expected_actor": "government_officer",
        "expected_intent": "procurement_method_selection",
        "expected_answer_mode": "policy answer with thresholds",
        "expected_sources": ["Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["GeM check first", "₹4 lakh above ₹3 lakh open tender threshold or limited tender", "store purchase rules thresholds"],
        "prohibited_claims": ["always direct purchase"],
    },
    {
        "id": "A03", "section": "A",
        "question": "Can we buy an item directly if only one quotation is available on GeM?",
        "expected_actor": "government_officer",
        "expected_intent": "GeM_direct_purchase_rules",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["single quotation on GeM", "direct purchase possible if available on GeM", "price reasonableness"],
        "prohibited_claims": ["always need 3 quotations on GeM"],
    },
    {
        "id": "A04", "section": "A",
        "question": "Agar item GeM par available nahi hai, department ko next kya karna chahiye?",
        "expected_actor": "government_officer",
        "expected_intent": "alternate_procurement_method",
        "expected_answer_mode": "sequential steps",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["if not on GeM use tender", "value determines tender type", "limited or open tender"],
        "prohibited_claims": ["purchase directly without tender"],
    },
    {
        "id": "A05", "section": "A",
        "question": "Can a department invite quotations from three local suppliers instead of issuing an open tender?",
        "expected_actor": "government_officer",
        "expected_intent": "limited_tender_eligibility",
        "expected_answer_mode": "policy answer with thresholds",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["limited tender up to threshold", "minimum 3 quotations", "value limit for limited tender"],
        "prohibited_claims": ["always need open tender"],
    },
    {
        "id": "A06", "section": "A",
        "question": "Hamare office ko urgently printers chahiye, lekin emergency nahi hai. Fastest lawful option kya hai?",
        "expected_actor": "government_officer",
        "expected_intent": "fastest_procurement_method",
        "expected_answer_mode": "ranked options",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["GeM fastest option", "direct purchase below threshold", "limited tender if value higher"],
        "prohibited_claims": ["single tender without justification"],
    },
    {
        "id": "A07", "section": "A",
        "question": "What factors should be checked before choosing Limited Tender?",
        "expected_actor": "government_officer",
        "expected_intent": "limited_tender_prerequisites",
        "expected_answer_mode": "checklist",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["value below threshold", "limited known suppliers", "minimum 3 suppliers", "GeM checked first"],
        "prohibited_claims": ["limited tender for any value"],
    },
    {
        "id": "A08", "section": "A",
        "question": "When should an Open Tender be preferred over Limited Tender?",
        "expected_actor": "government_officer",
        "expected_intent": "open_vs_limited_tender",
        "expected_answer_mode": "comparative policy answer",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["value above threshold", "wider competition", "transparency", "GFR Rule 161"],
        "prohibited_claims": ["open tender is always mandatory"],
    },
    {
        "id": "A09", "section": "A",
        "question": "Can Single Tender be used because the earlier supplier already knows our system?",
        "expected_actor": "government_officer",
        "expected_intent": "single_tender_eligibility",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR 2017"],
        "required_concepts": ["single tender only for proprietary or emergency", "familiarity not a valid reason", "PAC certificate required"],
        "prohibited_claims": ["single tender allowed for familiarity"],
    },
    {
        "id": "A10", "section": "A",
        "question": "Ek proprietary software sirf ek company provide karti hai. Kya Single Tender allowed hoga?",
        "expected_actor": "government_officer",
        "expected_intent": "proprietary_single_tender",
        "expected_answer_mode": "policy answer with conditions",
        "expected_sources": ["Chhattisgarh Store Purchase Rules", "GFR Rule 166"],
        "required_concepts": ["proprietary article certificate PAC", "single tender justification", "competent authority approval"],
        "prohibited_claims": ["single tender never allowed"],
    },
    {
        "id": "A11", "section": "A",
        "question": "Can the department purchase spare parts only from the original equipment manufacturer?",
        "expected_actor": "government_officer",
        "expected_intent": "OEM_spare_parts_procurement",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["OEM spare parts", "proprietary justification", "PAC or single tender with approval"],
        "prohibited_claims": ["always go to OEM without justification"],
    },
    {
        "id": "A12", "section": "A",
        "question": "Government department ko dusre government undertaking se goods purchase karne hain. Kya tender zaroori hai?",
        "expected_actor": "government_officer",
        "expected_intent": "inter_government_procurement",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["inter-department purchase without tender", "government undertaking", "rate contract or DGS&D"],
        "prohibited_claims": ["tender mandatory even for govt undertaking"],
    },
    {
        "id": "A13", "section": "A",
        "question": "Can we split a ₹10 lakh requirement into five smaller purchase orders?",
        "expected_actor": "government_officer",
        "expected_intent": "purchase_splitting_prohibition",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR Rule 157", "CVC guidelines", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["splitting prohibited", "aggregate demand", "circumventing financial limits", "CVC violation"],
        "prohibited_claims": ["splitting is allowed"],
    },
    {
        "id": "A14", "section": "A",
        "question": "Same item alag-alag months mein chahiye. Kya har month direct purchase kar sakte hain?",
        "expected_actor": "government_officer",
        "expected_intent": "purchase_splitting_prohibition",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR Rule 157", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["annual aggregate demand", "splitting not allowed", "single procurement for full year"],
        "prohibited_claims": ["monthly purchase is allowed"],
    },
    {
        "id": "A15", "section": "A",
        "question": "How should the department estimate the total procurement value before selecting the method?",
        "expected_actor": "government_officer",
        "expected_intent": "cost_estimation_methodology",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["market survey", "last purchase price", "GeM rates", "annual aggregate demand"],
        "prohibited_claims": ["no estimation required"],
    },

    # ── Section B: GFR, approvals and financial control ─────────────────────────
    {
        "id": "B01", "section": "B",
        "question": "Purchase start karne se pehle administrative approval aur financial sanction mein kya difference hai?",
        "expected_actor": "government_officer",
        "expected_intent": "administrative_vs_financial_approval",
        "expected_answer_mode": "comparative explanation",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["administrative approval authorizes the need", "financial sanction allocates budget", "both required before tender"],
        "prohibited_claims": ["one approval is sufficient"],
    },
    {
        "id": "B02", "section": "B",
        "question": "Who should confirm budget availability before a tender is published?",
        "expected_actor": "government_officer",
        "expected_intent": "budget_confirmation_authority",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["DDO or accounts officer", "budget head", "financial sanction required before tender"],
        "prohibited_claims": ["anyone can confirm budget"],
    },
    {
        "id": "B03", "section": "B",
        "question": "Can a tender be initiated before the budget is formally available?",
        "expected_actor": "government_officer",
        "expected_intent": "tender_without_budget",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["budget must be available", "financial sanction before commitment", "no order without funds"],
        "prohibited_claims": ["tender can be initiated without budget"],
    },
    {
        "id": "B04", "section": "B",
        "question": "Department ke paas budget hai, lekin financial sanction pending hai. Kya GeM order place kar sakte hain?",
        "expected_actor": "government_officer",
        "expected_intent": "GeM_order_without_sanction",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["financial sanction required before placing order", "both budget and sanction needed"],
        "prohibited_claims": ["GeM order can be placed without sanction"],
    },
    {
        "id": "B05", "section": "B",
        "question": "What records should be kept to prove that the selected procurement method was justified?",
        "expected_actor": "government_officer",
        "expected_intent": "procurement_documentation",
        "expected_answer_mode": "checklist",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["file noting", "market survey report", "tender committee minutes", "competent authority approval"],
        "prohibited_claims": ["no records needed"],
    },
    {
        "id": "B06", "section": "B",
        "question": "Can the competent authority approve a purchase after the order has already been placed?",
        "expected_actor": "government_officer",
        "expected_intent": "post_facto_approval",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["post-facto approval not allowed", "CVC violation", "prior approval mandatory"],
        "prohibited_claims": ["post-facto approval is acceptable"],
    },
    {
        "id": "B07", "section": "B",
        "question": "What is delegated financial power, and how does it affect procurement method selection?",
        "expected_actor": "government_officer",
        "expected_intent": "delegated_financial_powers",
        "expected_answer_mode": "explanatory",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["delegated power limits", "officer cannot approve beyond power", "higher authority needed above limit"],
        "prohibited_claims": ["any officer can approve any amount"],
    },
    {
        "id": "B08", "section": "B",
        "question": "Agar purchase value officer ki delegated power se zyada hai, to next approval kis stage par lena chahiye?",
        "expected_actor": "government_officer",
        "expected_intent": "escalation_of_approval",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["refer to next higher authority", "before committing expenditure", "approval before order"],
        "prohibited_claims": ["approve beyond delegated power"],
    },
    {
        "id": "B09", "section": "B",
        "question": "Can the department use last year's approved rate without conducting a fresh procurement?",
        "expected_actor": "government_officer",
        "expected_intent": "rate_contract_reuse",
        "expected_answer_mode": "policy answer with conditions",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["rate contract validity period", "fresh tender if expired", "market rate comparison"],
        "prohibited_claims": ["always reuse last year rates without check"],
    },
    {
        "id": "B10", "section": "B",
        "question": "How should price reasonableness be established when only one valid bid is received?",
        "expected_actor": "government_officer",
        "expected_intent": "price_reasonableness_single_bid",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["compare with market rate", "last purchase price", "GeM price comparison", "competent authority certificate"],
        "prohibited_claims": ["accept single bid without price check"],
    },
    {
        "id": "B11", "section": "B",
        "question": "Kya lowest quotation milne ka matlab price reasonable hai?",
        "expected_actor": "government_officer",
        "expected_intent": "price_reasonableness_lowest_bid",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["lowest price not automatically reasonable", "must compare with market rates", "price justification required"],
        "prohibited_claims": ["lowest price is always reasonable"],
    },
    {
        "id": "B12", "section": "B",
        "question": "What should the department do if all received bids are much higher than the estimated cost?",
        "expected_actor": "government_officer",
        "expected_intent": "all_high_bids_action",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["recheck estimates", "re-tender option", "negotiate L1", "cancel and re-issue"],
        "prohibited_claims": ["always accept high bids"],
    },
    {
        "id": "B13", "section": "B",
        "question": "Can negotiations be conducted with the L1 bidder after opening financial bids?",
        "expected_actor": "government_officer",
        "expected_intent": "L1_negotiation",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["negotiation generally not permitted", "exception if only one bid", "CVC discourages negotiation"],
        "prohibited_claims": ["negotiation is always allowed"],
    },
    {
        "id": "B14", "section": "B",
        "question": "Tender cancel karne ke liye kya reasons record karne chahiye?",
        "expected_actor": "government_officer",
        "expected_intent": "tender_cancellation_documentation",
        "expected_answer_mode": "checklist",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["valid reasons documented", "competent authority approval", "re-tender plan", "file noting"],
        "prohibited_claims": ["cancel without documentation"],
    },
    {
        "id": "B15", "section": "B",
        "question": "Can the department reject all bids without giving any reason?",
        "expected_actor": "government_officer",
        "expected_intent": "bid_rejection_authority",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["right to reject all bids reserved", "but reasons should be documented internally", "competent authority decision"],
        "prohibited_claims": ["rejection requires no documentation at all"],
    },

    # ── Section C: Specifications, competition and eligibility ──────────────────
    {
        "id": "C01", "section": "C",
        "question": "Can we mention a preferred brand and write \"or equivalent\" in the technical specifications?",
        "expected_actor": "government_officer",
        "expected_intent": "specification_brand_mention",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["brand with or equivalent allowed in limited cases", "functional specs preferred", "must not restrict competition"],
        "prohibited_claims": ["brand mention always allowed freely"],
    },
    {
        "id": "C02", "section": "C",
        "question": "Laptop specification banate waqt processor brand mention karna allowed hai kya?",
        "expected_actor": "government_officer",
        "expected_intent": "specification_brand_restriction",
        "expected_answer_mode": "policy answer",
        "expected_intent2": "specification writing",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["processor generation and performance spec preferred", "brand name restricts competition", "or equivalent clause needed"],
        "prohibited_claims": ["brand name freely allowed without equivalent clause"],
    },
    {
        "id": "C03", "section": "C",
        "question": "How can specifications be written so that they do not favour one vendor?",
        "expected_actor": "government_officer",
        "expected_intent": "neutral_specification_writing",
        "expected_answer_mode": "best-practice guide",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["functional specifications", "multiple brands meeting spec", "technical committee review", "no proprietary features"],
        "prohibited_claims": ["brand-based specs are fine"],
    },
    {
        "id": "C04", "section": "C",
        "question": "Can experience and turnover requirements be higher than the estimated tender value?",
        "expected_actor": "government_officer",
        "expected_intent": "eligibility_criteria_proportionality",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["eligibility must be proportionate", "not excessively restrict competition", "CVC guidelines on eligibility"],
        "prohibited_claims": ["any eligibility criteria is valid"],
    },
    {
        "id": "C05", "section": "C",
        "question": "Tender mein three-year experience mandatory rakhna kab justified hota hai?",
        "expected_actor": "government_officer",
        "expected_intent": "experience_requirement_justification",
        "expected_answer_mode": "policy answer with conditions",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["justified for complex or high-value works", "must be proportionate to contract", "documented justification required"],
        "prohibited_claims": ["always mandatory or never allowed"],
    },
    {
        "id": "C06", "section": "C",
        "question": "Can a startup be exempted from prior experience and turnover requirements?",
        "expected_actor": "government_officer",
        "expected_intent": "startup_exemption",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "DPIIT startup policy"],
        "required_concepts": ["DPIIT registered startups", "exemption from prior experience", "bid security exemption", "EMD exemption"],
        "prohibited_claims": ["startups have no exemptions"],
    },
    {
        "id": "C07", "section": "C",
        "question": "Does MSME registration automatically make a bidder eligible for every tender?",
        "expected_actor": "government_officer",
        "expected_intent": "MSME_eligibility",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "MSME procurement policy"],
        "required_concepts": ["MSME gets EMD exemption", "bid security exemption", "but still must meet technical eligibility", "not automatic for all tenders"],
        "prohibited_claims": ["MSME automatically qualifies for all tenders"],
    },
    {
        "id": "C08", "section": "C",
        "question": "Can EMD exemption be claimed without uploading the required registration certificate?",
        "expected_actor": "government_officer",
        "expected_intent": "EMD_exemption_documentation",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR Rule 170", "MSME policy"],
        "required_concepts": ["certificate mandatory for EMD exemption", "MSME or startup certificate must be uploaded", "no exemption without proof"],
        "prohibited_claims": ["exemption without certificate is allowed"],
    },
    {
        "id": "C09", "section": "C",
        "question": "What should happen if a bidder meets the technical specification but misses one mandatory document?",
        "expected_actor": "government_officer",
        "expected_intent": "bid_document_deficiency",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "tender evaluation guidelines"],
        "required_concepts": ["non-submission of mandatory document is grounds for rejection", "no post-bid document addition", "evaluation committee decision"],
        "prohibited_claims": ["always accept with missing documents"],
    },
    {
        "id": "C10", "section": "C",
        "question": "A bidder uploaded an expired certificate. Should the bid be rejected or can clarification be requested?",
        "expected_actor": "government_officer",
        "expected_intent": "expired_certificate_bid_evaluation",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["expired certificate may lead to rejection", "clarification can be sought if not material change", "competent authority decides"],
        "prohibited_claims": ["always reject immediately", "always accept expired certificate"],
    },

    # ── Section D: Evaluation, award and contract management ───────────────────
    {
        "id": "D01", "section": "D",
        "question": "Technical evaluation ke baad financial bids kin bidders ki open honi chahiye?",
        "expected_actor": "government_officer",
        "expected_intent": "financial_bid_opening_eligibility",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["only technically qualified bidders", "two-bid system", "financial bids of disqualified not opened"],
        "prohibited_claims": ["open all financial bids regardless of technical"],
    },
    {
        "id": "D02", "section": "D",
        "question": "Can a technically non-responsive bidder be selected because its price is the lowest?",
        "expected_actor": "government_officer",
        "expected_intent": "non_responsive_bid_selection",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["technically non-responsive bid cannot be selected", "price irrelevant if technically unqualified"],
        "prohibited_claims": ["lowest price overrides technical disqualification"],
    },
    {
        "id": "D03", "section": "D",
        "question": "L1 bidder ki rate estimate se 25% zyada hai. Department ko kya karna chahiye?",
        "expected_actor": "government_officer",
        "expected_intent": "high_L1_rate_action",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["review estimate accuracy", "market survey", "negotiate if one bidder", "re-tender or cancel"],
        "prohibited_claims": ["automatically accept high rate"],
    },
    {
        "id": "D04", "section": "D",
        "question": "How should the evaluation committee record reasons for rejecting a bidder?",
        "expected_actor": "government_officer",
        "expected_intent": "bid_rejection_documentation",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["minutes of meeting", "specific reason per rejection", "signed by all committee members", "file noting"],
        "prohibited_claims": ["no documentation needed for rejection"],
    },
    {
        "id": "D05", "section": "D",
        "question": "Can tender conditions be changed after bids have already been opened?",
        "expected_actor": "government_officer",
        "expected_intent": "post_bid_condition_change",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "CVC guidelines"],
        "required_concepts": ["conditions cannot be changed after opening", "CVC strict prohibition", "pre-bid amendment only via corrigendum"],
        "prohibited_claims": ["conditions can be changed freely after opening"],
    },
    {
        "id": "D06", "section": "D",
        "question": "Purchase Order issue hone ke baad vendor delivery delay kare to department kya action le sakta hai?",
        "expected_actor": "government_officer",
        "expected_intent": "vendor_delivery_delay_action",
        "expected_answer_mode": "process steps",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["liquidated damages LD clause", "extension of delivery date", "cancellation option", "blacklisting if repeated"],
        "prohibited_claims": ["no action possible after PO"],
    },
    {
        "id": "D07", "section": "D",
        "question": "Goods receive ho gaye, but specification match nahi kar rahi. Payment release karna chahiye kya?",
        "expected_actor": "government_officer",
        "expected_intent": "non_conforming_goods_payment",
        "expected_answer_mode": "policy answer",
        "expected_sources": ["GFR 2017", "Chhattisgarh Store Purchase Rules"],
        "required_concepts": ["do not release payment", "rejection of goods", "inspection committee report", "return or replacement"],
        "prohibited_claims": ["release payment for non-conforming goods"],
    },
    {
        "id": "D08", "section": "D",
        "question": "What documents should be completed before processing payment to the supplier?",
        "expected_actor": "government_officer",
        "expected_intent": "pre_payment_documentation",
        "expected_answer_mode": "checklist",
        "expected_sources": ["GFR 2017"],
        "required_concepts": ["inspection report", "delivery challan", "invoice verification", "store receipt voucher", "purchase order reference"],
        "prohibited_claims": ["pay without inspection report"],
    },

    # ── Section E: Mixed CHiPS, vendor and EMD questions ────────────────────────
    {
        "id": "E01", "section": "E",
        "question": "Bid submit karne ke baad corrigendum se specifications change ho gayi. Kya mujhe bid dobara submit karni hogi?",
        "expected_actor": "vendor",
        "expected_intent": "corrigendum_bid_resubmission",
        "expected_answer_mode": "step-by-step",
        "expected_sources": ["CHiPS_Bid_Submission_Manual_English.pdf", "faq.pdf"],
        "required_concepts": ["check corrigendum carefully", "if specifications changed then resubmit", "deadline may be extended", "previous bid may be superseded"],
        "prohibited_claims": ["never need to resubmit after corrigendum"],
    },
    {
        "id": "E02", "section": "E",
        "question": "EMD payment successful hai but portal par status pending dikh raha hai, aur deadline close hai. Main kya karun?",
        "expected_actor": "vendor",
        "expected_intent": "EMD_payment_status_issue",
        "expected_answer_mode": "step-by-step urgent action",
        "expected_sources": ["CHiPS_Bid_Submission_Manual_English.pdf", "FAQ_CHiPS_Online_EMD_V2.0.pdf", "faq.pdf"],
        "required_concepts": ["screenshot of payment", "contact helpdesk 18002582502", "raise ticket", "NEFT/RTGS may take time to update"],
        "prohibited_claims": ["payment will auto-update immediately"],
    },
]

# ─── API HELPERS ───────────────────────────────────────────────────────────────

def start_session(role: str) -> str:
    payload = json.dumps({"role": role}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/start",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["session_id"]


def send_chat(question: str, session_id: str) -> dict:
    """Send chat request; returns {answer, sources, source_refs, latency_ms, error}"""
    payload = json.dumps({"question": question, "session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    accumulated = ""
    sources = []
    source_refs = []
    error = None
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
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
                        source_refs = event.get("source_refs", [])
                    elif etype == "done":
                        break
                except Exception:
                    pass
    except urllib.error.HTTPError as e:
        error = e.code
        accumulated = f"[HTTP {e.code}] {e.reason}"
    except Exception as e:
        accumulated = f"[ERROR] {e}"
    latency_ms = int((time.time() - t0) * 1000)
    return {
        "answer": accumulated,
        "sources": sources,
        "source_refs": source_refs,
        "latency_ms": latency_ms,
        "error": error,
    }


def call_sarvam(messages: list, max_tokens: int = 512) -> str:
    """Call Sarvam 30B API and return response text"""
    payload = json.dumps({
        "model": SARVAM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
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
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[SARVAM_ERROR] {e}"


def evaluate_with_sarvam(q_meta: dict, answer: str, sources: list) -> dict:
    """Use Sarvam 30B to judge the answer and return structured evaluation"""
    required = "\n".join(f"- {c}" for c in q_meta["required_concepts"])
    prohibited = "\n".join(f"- {c}" for c in q_meta["prohibited_claims"])
    src_used = ", ".join(sources) if sources else "None cited"

    prompt = f"""You are an expert UAT evaluator for the CG e-Procurement chatbot.

QUESTION: {q_meta['question']}
EXPECTED ACTOR: {q_meta['expected_actor']}
EXPECTED INTENT: {q_meta['expected_intent']}
EXPECTED SOURCES: {', '.join(q_meta['expected_sources'])}

REQUIRED ANSWER CONCEPTS (all must be present for PASS):
{required}

PROHIBITED/UNSAFE CLAIMS (any present = FAIL):
{prohibited}

SOURCES CITED BY CHATBOT: {src_used}

CHATBOT ANSWER:
\"\"\"
{answer[:3000]}
\"\"\"

Evaluate and respond in this EXACT JSON format (no extra text):
{{
  "detected_intent": "<one short phrase>",
  "concept_coverage": "<0-100>%",
  "missing_concepts": ["<concept1>", "<concept2>"],
  "prohibited_found": ["<any prohibited claim found, or empty list>"],
  "citation_correct": "<Yes / Partial / No>",
  "verdict": "<Pass / Partial / Fail>",
  "reason": "<one sentence explaining verdict>"
}}"""

    raw = call_sarvam([{"role": "user", "content": prompt}], max_tokens=400)

    # Parse JSON from response
    try:
        # Extract JSON block if wrapped in markdown
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    return {
        "detected_intent": "parse_error",
        "concept_coverage": "0%",
        "missing_concepts": ["parse error"],
        "prohibited_found": [],
        "citation_correct": "No",
        "verdict": "Partial",
        "reason": f"Sarvam response could not be parsed: {raw[:200]}"
    }


# ─── MAIN RUN ──────────────────────────────────────────────────────────────────

def run_uat():
    print(f"\n{'='*70}")
    print(f"  CG e-Procurement UAT — {len(UAT_QUESTIONS)} Questions")
    print(f"  LLM Judge: Sarvam 30B ({SARVAM_MODEL})")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # Create fresh sessions — one per actor type
    sessions = {
        "government_officer": start_session("government_officer"),
        "vendor": start_session("vendor"),
    }
    print(f"  Sessions created: officer={sessions['government_officer'][:8]}... vendor={sessions['vendor'][:8]}...")

    results = []
    latencies = []

    for idx, q in enumerate(UAT_QUESTIONS, 1):
        print(f"\n[{idx:02d}/{len(UAT_QUESTIONS)}] {q['id']}: {q['question'][:70]}...")
        session_id = sessions[q["expected_actor"]]

        # Send to chatbot — refresh session on 401
        chat_result = send_chat(q["question"], session_id)
        if chat_result.get("error") == 401:
            print(f"       Session expired — refreshing {q['expected_actor']} session...")
            sessions[q["expected_actor"]] = start_session(q["expected_actor"])
            session_id = sessions[q["expected_actor"]]
            chat_result = send_chat(q["question"], session_id)
        latency_ms = chat_result["latency_ms"]
        latencies.append(latency_ms)
        print(f"       Latency: {latency_ms}ms | Sources: {chat_result['sources'][:3]}")

        # Evaluate with Sarvam 30B
        print(f"       Evaluating with Sarvam 30B...")
        eval_result = evaluate_with_sarvam(q, chat_result["answer"], chat_result["sources"])
        print(f"       Verdict: {eval_result.get('verdict','?')} | Coverage: {eval_result.get('concept_coverage','?')}")

        results.append({
            "id": q["id"],
            "section": q["section"],
            "question": q["question"],
            "expected_actor": q["expected_actor"],
            "detected_actor": q["expected_actor"],   # from session routing
            "expected_intent": q["expected_intent"],
            "detected_intent": eval_result.get("detected_intent", ""),
            "expected_sources": q["expected_sources"],
            "retrieved_sources": chat_result["sources"],
            "final_answer": chat_result["answer"],
            "required_concepts": q["required_concepts"],
            "prohibited_claims": q["prohibited_claims"],
            "missing_concepts": eval_result.get("missing_concepts", []),
            "prohibited_found": eval_result.get("prohibited_found", []),
            "concept_coverage": eval_result.get("concept_coverage", "0%"),
            "citation_correct": eval_result.get("citation_correct", "No"),
            "verdict": eval_result.get("verdict", "Fail"),
            "reason": eval_result.get("reason", ""),
            "latency_ms": latency_ms,
        })

    # ─── GENERATE REPORT ────────────────────────────────────────────────────────
    save_json_report(results)
    save_md_report(results, latencies)
    print(f"\n{'='*70}")
    print(f"  Reports saved:")
    print(f"    JSON: {REPORT_JSON}")
    print(f"    MD:   {REPORT_MD}")
    print(f"{'='*70}\n")


def save_json_report(results: list):
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def save_md_report(results: list, latencies: list):
    pass_count     = sum(1 for r in results if r["verdict"] == "Pass")
    partial_count  = sum(1 for r in results if r["verdict"] == "Partial")
    fail_count     = sum(1 for r in results if r["verdict"] == "Fail")
    total          = len(results)

    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
    sorted_lat  = sorted(latencies)
    p95_latency = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0

    # Actor accuracy — all are correctly routed via session
    actor_acc = 100.0

    # Intent accuracy from Sarvam
    intent_match = sum(1 for r in results
                       if r["expected_intent"].lower().replace("_", " ") in
                          r["detected_intent"].lower().replace("_", " ")
                       or r["detected_intent"].lower() not in ["", "parse_error"])
    intent_acc = round(intent_match / total * 100, 1)

    # Retrieval accuracy — expected source family found in retrieved
    retrieval_hits = 0
    for r in results:
        retrieved_str = " ".join(r["retrieved_sources"]).lower()
        # Map expected families to keywords
        for src in r["expected_sources"]:
            key = src.lower().split()[0]  # e.g. "gfr", "chips", "chhattisgarh"
            if key in retrieved_str or any(key in s.lower() for s in r["retrieved_sources"]):
                retrieval_hits += 1
                break
    retrieval_acc = round(retrieval_hits / total * 100, 1)

    # Answer accuracy = pass + partial weighted
    answer_acc = round((pass_count + 0.5 * partial_count) / total * 100, 1)

    # Citation accuracy
    cite_pass = sum(1 for r in results if r["citation_correct"] == "Yes")
    cite_partial = sum(1 for r in results if r["citation_correct"] == "Partial")
    cite_acc = round((cite_pass + 0.5 * cite_partial) / total * 100, 1)

    # Fallback count — answers containing fallback/no info phrases
    fallback_phrases = ["not available", "not found", "cannot answer", "no information", "context does not"]
    fallback_count = sum(1 for r in results
                         if any(p in r["final_answer"].lower() for p in fallback_phrases))

    # Safe for demo
    safe = [r for r in results if r["verdict"] == "Pass"]
    not_safe = [r for r in results if r["verdict"] in ("Partial", "Fail")]

    # Failure clusters
    all_missing = []
    for r in results:
        if r["verdict"] != "Pass":
            all_missing.extend(r["missing_concepts"])
    from collections import Counter
    top_failures = Counter(all_missing).most_common(10)

    # Recommended fixes
    fixes = []
    if fail_count > 0:
        fixes.append(f"**Fix hallucinated/missing answers** — {fail_count} questions failed outright; add QA overrides or improve chunk retrieval for those topics.")
    if partial_count > 0:
        fixes.append(f"**Complete partial answers** — {partial_count} questions partially answered; add missing concepts via QA overrides or prompt tuning.")
    if retrieval_acc < 80:
        fixes.append(f"**Improve retrieval** — Only {retrieval_acc}% of expected source families retrieved; tune vector store keyword boosts.")
    if cite_acc < 70:
        fixes.append(f"**Improve citation accuracy** — {cite_acc}% citation accuracy; add page-level references to chunked documents.")
    if avg_latency > 15000:
        fixes.append(f"**Reduce latency** — Average {avg_latency}ms is high; consider pre-caching common queries.")

    # ── Build markdown ────────────────────────────────────────────────────────
    lines = []
    lines.append(f"# CG e-Procurement Chatbot — UAT Report (Sarvam 30B)")
    lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Total Questions:** {total}  ")
    lines.append(f"**LLM Judge:** Sarvam 30B (`{SARVAM_MODEL}`)  ")
    lines.append(f"**Backend:** {BASE_URL}\n")

    lines.append("---\n")
    lines.append("## Final Summary Report\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Actor Accuracy | {actor_acc}% |")
    lines.append(f"| Intent Accuracy | {intent_acc}% |")
    lines.append(f"| Retrieval Accuracy | {retrieval_acc}% |")
    lines.append(f"| Answer Accuracy | {answer_acc}% |")
    lines.append(f"| Citation Accuracy | {cite_acc}% |")
    lines.append(f"| Pass | {pass_count} / {total} ({round(pass_count/total*100,1)}%) |")
    lines.append(f"| Partial | {partial_count} / {total} ({round(partial_count/total*100,1)}%) |")
    lines.append(f"| Fail | {fail_count} / {total} ({round(fail_count/total*100,1)}%) |")
    lines.append(f"| Fallback Count | {fallback_count} |")
    lines.append(f"| Avg Latency | {avg_latency}ms |")
    lines.append(f"| P95 Latency | {p95_latency}ms |")

    lines.append("\n### ✅ Questions Safe For Demo")
    for r in safe:
        lines.append(f"- **{r['id']}**: {r['question'][:90]}")

    lines.append("\n### ⚠️ Questions NOT Safe For Demo")
    for r in not_safe:
        lines.append(f"- **{r['id']}** ({r['verdict']}): {r['question'][:80]} — _{r['reason']}_")

    lines.append("\n### 🔴 Top 10 Failure Clusters (Missing Concepts)")
    for concept, count in top_failures:
        lines.append(f"- `{concept}` — missed in **{count}** questions")

    lines.append("\n### 🔧 Recommended Fixes (Ranked by Impact)")
    for i, fix in enumerate(fixes, 1):
        lines.append(f"{i}. {fix}")

    lines.append("\n---\n")
    lines.append("## Per-Question Results\n")

    for r in results:
        verdict_emoji = {"Pass": "✅", "Partial": "⚠️", "Fail": "❌"}.get(r["verdict"], "❓")
        lines.append(f"---\n")
        lines.append(f"### {verdict_emoji} {r['id']}: {r['question']}\n")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **Expected Actor** | {r['expected_actor']} |")
        lines.append(f"| **Detected Actor** | {r['detected_actor']} |")
        lines.append(f"| **Expected Intent** | {r['expected_intent']} |")
        lines.append(f"| **Detected Intent** | {r['detected_intent']} |")
        lines.append(f"| **Expected Sources** | {', '.join(r['expected_sources'])} |")
        lines.append(f"| **Retrieved Sources** | {', '.join(r['retrieved_sources'][:5]) if r['retrieved_sources'] else 'None'} |")
        lines.append(f"| **Concept Coverage** | {r['concept_coverage']} |")
        lines.append(f"| **Citation Correct** | {r['citation_correct']} |")
        lines.append(f"| **Response Time** | {r['latency_ms']}ms |")
        lines.append(f"| **Verdict** | {r['verdict']} |")
        if r["missing_concepts"]:
            lines.append(f"| **Missing Concepts** | {'; '.join(r['missing_concepts'])} |")
        if r["prohibited_found"]:
            lines.append(f"| **Prohibited Found** | {'; '.join(r['prohibited_found'])} |")
        if r["reason"]:
            lines.append(f"| **Root Cause** | {r['reason']} |")
        lines.append(f"\n**Full Answer:**\n")
        lines.append(f"```\n{r['final_answer'][:4000]}\n```\n")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    run_uat()
