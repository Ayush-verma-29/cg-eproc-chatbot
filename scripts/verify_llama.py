# scripts/verify_llama.py
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Temporarily override settings config to use llama3.2:3b just in case
from app.core.config import settings
settings.TRANSLATION_MODEL = "llama3.2:3b"

from app.core.language import language_service

def verify():
    print(f"Verifying integrated translation service with {settings.TRANSLATION_MODEL}...")
    
    english_text = (
        "The provided context does not explicitly mention any rule number for \"short tenders\" or \"limited tendering\". "
        "However, it is mentioned that such tenders can be done without wide publicity in newspapers due to time constraints [Page 317]. "
        "Also, short-term / limited tenders are put on the website of the department as per Office Order No.98/ORD/1 dated 11th Feb., 2004 (applies to limited tenders also) [Clarification section].\n\n"
        "Regarding the process for such tenders, it is stated that they do not require publicity through newspapers and pre-qualified / known vendors are invited during the tender process. "
        "The details of terms can be obtained with the tender form from the concerned office within working days prior to the fixed date [Page 8].\n\n"
        "The contents of the Tender Document for any tendering method, including short or limited tenders, include sections such as Notice Inviting Tender (NIT), Instructions to Bidders (ITB), General Conditions of Contract (GCC), Special Conditions of Contract (SCC) and others [Page 317].\n\n"
        "The tender shall be submitted within the time table fixed in the online tender, and it will be opened as per that schedule. The tenders can be received by registered post or authorized courier [Page 9]."
    )
    
    res = language_service.translate_to_hindi(english_text)
    
    print("\n--- FINAL TRANSLATION ---")
    with open("scripts/verify_llama_output.txt", "w", encoding="utf-8") as f:
        f.write(res)
    print("Output written to scripts/verify_llama_output.txt")
    print("-------------------------")

if __name__ == "__main__":
    verify()
