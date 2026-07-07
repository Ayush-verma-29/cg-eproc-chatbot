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
