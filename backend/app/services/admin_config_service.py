# backend/app/services/admin_config_service.py
import json
import threading
from pathlib import Path
from app.core.config import settings

DEFAULT_CONFIG = {
    "deactivated_documents": [],
    "blacklist_rules": [],
    "engine_params": {
        "k": 7,
        "max_context_chars": 4000,
        "temperature": 0.0
    },
    "topic_boosts": {
        "emd": 25,
        "gfr": 20,
        "gem": 15,
        "cvc": 15,
        "registration": 12,
        "dsc": 10,
        "bid_submission": 18,
        "short_tender": 10,
        "service_procurement": 12,
        "msme": 15,
        "faq": 8
    },
    "qa_overrides": [],
    "hallucination_corrections": [
        {
            "query": "What is the mandatory online platform for purchasing goods in Chhattisgarh, and what should a department do if it wishes to buy items outside this platform?",
            "answer": "1. Mandatory Platform:\nThe Government e-Marketplace (GeM) portal is the mandatory platform. As per Rule 3.1.1 of the Chhattisgarh Store Purchase Rules, all government departments must procure goods, items, and services whose rates and specifications are available on GeM through the GeM website.\n\n2. Purchasing Outside GeM:\nIf a department wishes to procure items outside GeM, they must do so through the tender system under Rule 4 of the Chhattisgarh Store Purchase Rules, but only after obtaining written consent from the Finance Department through the concerned administrative department."
        },
        {
            "query": "If a government department in Chhattisgarh needs to procure an item available on the GeM portal but wants to purchase it through a different method, what approval is required before proceeding?",
            "answer": "As per Rule 3.1.1 of the Chhattisgarh Store Purchase Rules, written consent from the Finance Department (obtained through the concerned administrative department) is required before a department can procure GeM-available items through a different method."
        },
        {
            "query": "What is the maximum value limit for purchasing a proprietary article in Chhattisgarh through a single tender without inviting competition?",
            "answer": "As per Rule 4.3.1(a) of the Chhattisgarh Store Purchase Rules, the maximum limit for purchasing a proprietary article through a single tender without inviting competition is ₹50,000 (fifty thousand rupees) per year."
        },
        {
            "query": "If the value of a proprietary item exceeds the prescribed single tender limit, what additional steps must the procuring department follow?",
            "answer": "As per Rule 4.3.1(b) of the Chhattisgarh Store Purchase Rules, when the value exceeds ₹50,000, the department must follow these steps:\n1. Obtain a Proprietary Article Certificate (PAC) from the administrative department in the prescribed format (Parishisht-4).\n2. Publish a brief notice in newspapers and a detailed notice on the department website inviting objections.\n3. Provide a minimum of 30 days for other parties to raise objections.\n4. If objections are received, resolve them properly.\n5. Obtain rate justification from the proposed supplier.\n6. The Purchase Committee will review the rates and make recommendations.\n7. Obtain Competent authority approval before proceeding with the procurement."
        },
        {
            "query": "For procurement in Chhattisgarh, within what monetary range is the \"Limited Tender\" method applicable?",
            "answer": "As per Rule 4.3.2 of the Chhattisgarh Store Purchase Rules, the Limited Tender method is applicable for procurements where the estimated annual purchase amount is between ₹50,001 and ₹3,00,000 (fifty thousand one to three lakh rupees)."
        },
        {
            "query": "Can the Limited Tender method be used for procurements exceeding ₹3,00,000? If yes, under what exceptional circumstances?",
            "answer": "Under the Chhattisgarh Store Purchase Rules, the Limited Tender method is generally restricted to procurements up to ₹3,00,000. The rules do not explicitly specify exceptional circumstances for using Limited Tenders above ₹3,00,000. For procurements exceeding ₹3,00,000, the Open Tender method must be used as per Rule 4.3.3. (Note: Rule 4.14 allows for repeat purchase orders up to 25% of the original order quantity under certain conditions)."
        },
        {
            "query": "What is the minimum estimated value of procurement that requires an open, advertised tender in Chhattisgarh?",
            "answer": "As per Rule 4.3.3 of the Chhattisgarh Store Purchase Rules, the minimum estimated value of procurement that requires an open, advertised tender is ₹3,00,001 (three lakh one rupees) and above."
        },
        {
            "query": "For an open tender valued between ₹3,00,001 and ₹5,00,000, what newspaper publicity is required?",
            "answer": "As per Rule 4.3.3(1) of the Chhattisgarh Store Purchase Rules, for open tenders valued between ₹3,00,001 and ₹5,00,000, publicity must be done in one widely circulated local newspaper (स्थानीय स्तर के बहुप्रचारित एक समाचार पत्र में) at the local level."
        },
        {
            "query": "What percentage of the estimated purchase value must a bidder submit as EMD in Chhattisgarh?",
            "answer": "As per Rule 4.7(अ) of the Chhattisgarh Store Purchase Rules, the Earnest Money Deposit (EMD) must be 1% (one percent) of the estimated purchase value."
        },
        {
            "query": "Which categories of bidders are exempted from submitting an EMD in government procurement in Chhattisgarh?",
            "answer": "As per Rule 4.7(ब) of the Chhattisgarh Store Purchase Rules, the following categories are exempted from submitting EMD:\n1. Small and cottage industry units registered with the Industries Department in Chhattisgarh.\n2. Recognized startups established in Chhattisgarh that are recognized by the Government of India (as defined in the Industrial Policy 2014-19) and valid on the date of tender issuance.\n(Note: Under Rule 4.7(स), proof of registration must be submitted with the tender to claim this exemption)."
        },
        {
            "query": "What procurement preference is given to recognized startups in Chhattisgarh, and what is the maximum annual limit for this preference?",
            "answer": "As per Rule 13 of the Chhattisgarh Store Purchase Rules, recognized startups established in the state receive:\n1. 1% purchase preference of the total purchase amount, provided they match the L1 (lowest acceptable tender) rate and their quality is satisfactory.\n2. A maximum limit of ₹10 lakh per year for this preference.\n3. The preference is valid for 3 years from the date of production/incorporation."
        },
        {
            "query": "When procuring goods in Chhattisgarh, what priority must be given to products manufactured by SC, ST, and OBC entrepreneurs?",
            "answer": "As per Rule 13 of the Chhattisgarh Store Purchase Rules, if any goods are manufactured by small industries established in the state, Scheduled Castes (SC), Scheduled Tribes (ST), and Other Backward Classes (OBC) entrepreneurs:\nSuch goods must be compulsorily procured from these entrepreneurs, provided the price and quality are comparable and within the registered production capacity limits of the unit."
        },
        {
            "query": "What is the maximum quantity limit for a repeat purchase order in Chhattisgarh government procurement?",
            "answer": "As per Rule 4.14(3) of the Chhattisgarh Store Purchase Rules, the quantity of a repeat purchase order shall not exceed 25% (twenty-five percent) of the original order quantity."
        },
        {
            "query": "For how long can the validity of an existing rate contract be extended in Chhattisgarh before a new contract must be executed?",
            "answer": "As per the Note under Rule 7 of the Chhattisgarh Store Purchase Rules:\n- The validity of an existing rate contract can be extended by a maximum of 6 months by the Commerce and Industry Department.\n- The total validity period (including the original contract period and the extension period) shall not exceed 1 year and 6 months under any circumstances."
        },
        {
            "query": "If a supplier fails to deliver goods within the agreed time in Chhattisgarh, what penalty is imposed?",
            "answer": "As per Rule 4.13 of the Chhattisgarh Store Purchase Rules, if a supplier fails to deliver goods within the agreed time, a penalty of 2% per month (प्रतिमाह पेनाल्टी) shall be imposed. Only one extension of time can be granted by the competent authority of the purchasing department."
        },
        {
            "query": "Can the delivery timeline be extended after the contract is signed, and if so, what are the conditions for such extension?",
            "answer": "As per Rule 4.13 of the Chhattisgarh Store Purchase Rules, the delivery timeline can be extended only once by the competent authority of the purchasing department, subject to a penalty of 2% per month during the extension period."
        },
        {
            "query": "For an open tender valued between ₹10,00,001 and ₹20,00,000, what are the newspaper publicity requirements?",
            "answer": "As per Rule 4.3.3(3) of the Chhattisgarh Store Purchase Rules, for open tenders valued between ₹10,00,001 and ₹20,00,000, publicity must be done in two widely circulated state-level newspapers (प्रदेश स्तरीय बहुप्रचारित दो समाचार पत्रों में) and one national newspaper (राष्ट्रीय स्तर के एक समाचार पत्र में)."
        },
        {
            "query": "How does the publicity requirement change for a tender valued above ₹20,00,000?",
            "answer": "As per Rule 4.3.3(4) of the Chhattisgarh Store Purchase Rules, for open tenders valued above ₹20,00,000, publicity must be done in two widely circulated state-level newspapers (प्रदेश स्तरीय बहुप्रचारित दो समाचार पत्रों में) and two national newspapers (राष्ट्रीय स्तर के दो समाचार पत्रों में)."
        },
        {
            "query": "What is the time period allowed for the first, second, and third call of a limited tender in Chhattisgarh?",
            "answer": "As per Rule 4.5 of the Chhattisgarh Store Purchase Rules, the timeline allowed for a Limited Tender is:\n1. First Call: 15 days\n2. Second Call: 10 days\n3. Third Call: 5 days\n(Note: The timeline is calculated from the date of invitation/publication)."
        },
        {
            "query": "What is the timeline for the first call for an open tender valued above ₹10 lakhs and for a global tender?",
            "answer": "As per Rule 4.5 of the Chhattisgarh Store Purchase Rules:\n1. Open Tender valued above ₹10 Lakhs: The timeline for the first call is 30 days.\n2. Global Tender: The timeline for the first call is 45 days.\n(Note: These timelines are calculated from the date of publication of the tender notice)."
        },
        {
            "query": "Within how many hours must a Provisional Receipt Certificate (PRC) be issued after goods are received?",
            "answer": "As per the Note under Rule 11 of the Chhattisgarh Store Purchase Rules, the buyer must issue a Provisional Receipt Certificate (PRC) within 48 hours of receiving the goods."
        },
        {
            "query": "After the Consignee Receipt and Acceptance Certificate (CRAC) is issued, within how many days must the payment be made?",
            "answer": "As per the Note under Rule 11 of the Chhattisgarh Store Purchase Rules:\n1. Payment must be made within 10 days from the date of issuance of the Consignee Receipt and Acceptance Certificate (CRAC).\n2. Additionally, under the main provisions of Rule 11 for offline/general purchases, bill payment must be made within 20 days of receiving the goods and bills. Delayed payment without valid reasons may attract interest at prevailing bank rates."
        },
        {
            "query": "When a department proposes to procure a proprietary article in Chhattisgarh, how many days are provided for other parties to raise objections?",
            "answer": "As per Rule 4.3.1(ब)(2) of the Chhattisgarh Store Purchase Rules, a minimum of 30 days (न्यूनतम 30 दिवस) must be provided on the website and/or newspapers for other parties to raise objections."
        },
        {
            "query": "What document must be obtained from the administrative department before procuring an item through a single tender as a proprietary article?",
            "answer": "As per Rule 4.3.1(ब) of the Chhattisgarh Store Purchase Rules, a department must obtain a Proprietary Article Certificate (PAC) in the prescribed format (Parishisht-4) from the administrative department before proceeding with single-source proprietary procurement."
        },
        {
            "query": "In Chhattisgarh government procurement, which official is mandatorily required to be a member of the Purchase Committee?",
            "answer": "As per Rule 4.12 of the Chhattisgarh Store Purchase Rules, the Accounts Officer (लेखा अधिकारी/लेखा प्रभारी) of the department must be mandatorily included as a member of the Purchase Committee."
        },
        {
            "query": "Is the recommendation of the Purchase Committee binding on the competent authority, or can the authority take a different decision?",
            "answer": "As per Rule 4.12 of the Chhattisgarh Store Purchase Rules, the recommendations of the Purchase Committee are not binding on the competent authority. The authority can take a different decision, but they must record the reasons for doing so in writing."
        },
        {
            "query": "What specific benefits are provided to recognized startups when participating in government procurement in Chhattisgarh?",
            "answer": "As per Rule 13 and Rule 4.7(ब) of the Chhattisgarh Store Purchase Rules, recognized startups in the state receive:\n1. Earnest Money Deposit (EMD) Exemption.\n2. 1% purchase preference (up to a maximum of ₹10 lakh per year), provided they match the L1 rate and meet quality requirements.\n3. Relaxation of prior experience and turnover requirements."
        },
        {
            "query": "For how many years from incorporation are startups eligible for the procurement benefits in Chhattisgarh?",
            "answer": "As per Rule 13 of the Chhattisgarh Store Purchase Rules, startups are eligible for procurement benefits for 3 years from the date of production or incorporation."
        }
    ],
    "protected_terms": [
        "EMD", "DSC", "CPPP", "GFR", "GeM", "CRN", "Rule", 
        "Section", "Clause", "Portal", "PAN", "GST", "IFSC", "PWD", "L1"
    ],
    "translation_enabled": True,
    "vendor_prompt": (
        "You are an AI assistant for the Chhattisgarh e-Procurement Portal, helping VENDORS.\n\n"
        "**Instructions:**\n"
        "- Answer the user's question **completely and accurately** based ONLY on the provided context. Do NOT skip any relevant detail, condition, contact number, deadline, or exception present in the context.\n"
        "- Cite Rule/Clause/Chapter numbers ONLY if they are **explicitly written** in the context text. Do NOT infer or guess rule numbers. If no rule is cited in the context, simply omit any rule reference — do NOT write phrases like \"No specific rule\", \"No rule number\", \"Rule not specified\", or similar.\n"
        "{formatting_instructions}\n"
        "{gfr_rule_mapping_instructions}\n\n"
        "Context:\n"
        "{context}\n\n"
        "Question: {english_query}\n\n"
        "Answer (in English, point-by-point list format only, citing specific Rule/Clause numbers):"
    ),
    "officer_prompt": (
        "You are an AI assistant for the Chhattisgarh e-Procurement Portal, helping GOVERNMENT OFFICERS.\n\n"
        "**Instructions:**\n"
        "- Answer the user's question **completely and accurately** based ONLY on the provided context. Do NOT skip any relevant detail, condition, contact number, deadline, or exception present in the context.\n"
        "- Cite Rule/Clause/Chapter numbers ONLY if they are **explicitly written** in the context text. Do NOT infer or guess rule numbers. If no rule is cited in the context, simply omit any rule reference — do NOT write phrases like \"No specific rule\", \"No rule number\", \"Rule not specified\", or similar.\n"
        "{formatting_instructions}\n"
        "{gfr_rule_mapping_instructions}\n\n"
        "Context:\n"
        "{context}\n\n"
        "Question: {english_query}\n\n"
        "Answer (in English, point-by-point list format only, citing specific Rule/Clause numbers):"
    ),
    "unified_prompt": (
        "You are an AI assistant for the Chhattisgarh e-Procurement Portal.\n"
        "The context below is drawn from the Chhattisgarh Store Purchase Rules 2002 [Govt Rules] (which is the PRIMARY, highest-priority document for state procurement) and GFR 2017 / other guidelines (which are secondary).\n\n"
        "**CRITICAL INSTRUCTIONS TO PREVENT HALLUCINATIONS:**\n"
        "- Base your answer ONLY on the provided context. Do NOT use external knowledge.\n"
        "- ALWAYS prioritize the Chhattisgarh Store Purchase Rules [Govt Rules] over GFR 2017.\n"
        "- NEVER fabricate rule numbers, clause numbers, or upload notice numbers. Only cite specific rules, clauses, or annexures if they are explicitly written in the context. If the context does not explicitly mention a rule number for a fact, do not include any rule citation.\n"
        "- Do not make up reference codes or notice numbers (e.g., do NOT invent codes like 'Notice No. 5L8VN20' or 'Upload Notice No. 5L8VN20').\n"
        "- Do not ask follow-up questions when the user is asking a general rule question.\n\n"
        "**Response Format:**\n"
        "{formatting_instructions}\n"
        "{gfr_rule_mapping_instructions}\n"
        "{abbreviation_instructions}\n\n"
        "--- ONE-SHOT EXAMPLE FOR PURCHASING GOODS ---\n"
        "User Query: I want to buy 3 laptops costing around 2 Lakhs\n"
        "Answer:\n"
        "1. Understand the Procurement Route (Threshold Rule)\n"
        "Under the Chhattisgarh Store Purchase Rules, since your estimated purchase value is ₹2 Lakhs (which is between ₹50,001 and ₹3,00,000), this falls under the Limited Tender threshold.\n\n"
        "2. Step-by-Step Purchase Guide (Mandatory GeM/e-Manak Route)\n"
        "Procurement must be done through the Government e-Marketplace (GeM) portal or the state portal (e-Manak) if available:\n"
        "- Login to your buyer account on the portal.\n"
        "- Compare at least 3 different manufacturers/sellers.\n"
        "- Select the L1 (Lowest Price) seller among the compared options.\n\n"
        "3. Alternative: Purchasing Outside GeM (Local Purchase Committee)\n"
        "If the laptops are not available on GeM/e-Manak:\n"
        "- Generate a GeMARPTS non-availability certificate from the portal.\n"
        "- Establish a Local Purchase Committee consisting of three members, including the Accounts Officer.\n"
        "- Obtain written quotations from at least 3 different local suppliers.\n"
        "- Purchase from the lowest-priced (L1) supplier meeting specifications.\n"
        "---------------------------------------------\n\n"
        "Context:\n"
        "{context}\n\n"
        "Question: {english_query}\n\n"
        "Answer (in English, point-by-point list format only, citing specific Rule/Clause numbers):"
    )
}

class AdminConfigService:
    def __init__(self):
        self.file_path = settings.DATA_DIR / "admin_config.json"
        self.lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        with self.lock:
            if not self.file_path.exists():
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)

    def get_config(self) -> dict:
        with self.lock:
            try:
                if self.file_path.exists():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Ensure all default keys are present in loaded config
                        updated = False
                        for k, v in DEFAULT_CONFIG.items():
                            if k not in data:
                                data[k] = v
                                updated = True
                        if updated:
                            with open(self.file_path, "w", encoding="utf-8") as wf:
                                json.dump(data, wf, indent=2, ensure_ascii=False)
                        return data
            except Exception as e:
                print(f"Error reading admin config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self, config_data: dict) -> bool:
        with self.lock:
            try:
                # Sanitize / ensure correct formatting of input parameters
                clean_config = DEFAULT_CONFIG.copy()
                for key in clean_config.keys():
                    if key in config_data:
                        clean_config[key] = config_data[key]
                
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(clean_config, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"Error saving admin config: {e}")
                return False

admin_config_service = AdminConfigService()
