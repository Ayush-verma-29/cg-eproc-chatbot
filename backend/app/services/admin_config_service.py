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
    "hallucination_corrections": [],
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
        "The context below is drawn from both the Vendor Manual [Vendor Manual] and Government Rules [Govt Rules]. "
        "Use the most relevant information to answer the question, regardless of which source it comes from.\n\n"
        "**Instructions:**\n"
        "- Answer the user's question **completely and accurately** based ONLY on the provided context.\n"
        "- When referencing Vendor Manual content, mention it applies to vendors/contractors. When referencing Govt Rules, note the Rule/Clause number.\n"
        "- Cite Rule/Clause/Chapter numbers ONLY if they are **explicitly written** in the context text. Do NOT infer or guess rule numbers.\n"
        "- If the user asks how to buy, purchase, or procure a specific item, follow the reasoning and response structure shown in the One-Shot Example below.\n"
        "{formatting_instructions}\n"
        "{gfr_rule_mapping_instructions}\n"
        "{abbreviation_instructions}\n\n"
        "--- ONE-SHOT EXAMPLE FOR PURCHASING GOODS ---\n"
        "User Query: I want to buy 3 air conditioners for our office costing around 1.5 Lakhs\n"
        "Answer:\n"
        "1. Understand the Procurement Route (Threshold Rule)\n"
        "Since your total procurement value (under 1.5 Lakh) is below the threshold for public tenders "
        "(which is Rs. 2.5 Lakh / Rs. 5 Lakh depending on the department), you do not need to publish a public e-tender. "
        "Instead, you can procure them directly or through comparative bidding on GeM.\n\n"
        "2. Step-by-Step Purchase Guide (Mandatory GeM Route)\n"
        "Under GFR Rule 149, procurement of standard goods through the Government e-Marketplace (GeM) is mandatory:\n"
        "Since the value is between Rs. 50,000 and Rs. 2.5 Lakhs:\n"
        "- Login to your buyer account on the GeM Portal.\n"
        "- Search for goods matching your required technical specifications.\n"
        "- You must select and compare at least 3 different manufacturers/sellers on the portal.\n"
        "- Place the order with the L1 (Lowest Price) seller among the compared options.\n\n"
        "3. Alternative: Purchasing Outside GeM (Local Purchase Committee)\n"
        "If the goods of your required specifications are not available on GeM:\n"
        "- You must generate a GeMARPTS (GeM Availability Report and Past Transaction Summary) certificate from the GeM portal to prove non-availability.\n"
        "- Under Rule 155 of GFR 2017, you can then purchase outside GeM via a Local Purchase Committee (LPC).\n"
        "- LPC Process:\n"
        "  - Form a 3-member committee of officers.\n"
        "  - The committee will survey the market to identify reliable suppliers.\n"
        "  - Obtain written quotations from at least 3 different local vendors.\n"
        "  - The committee will prepare a comparative statement and recommend purchasing from the lowest-priced (L1) supplier who meets the specifications.\n"
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
