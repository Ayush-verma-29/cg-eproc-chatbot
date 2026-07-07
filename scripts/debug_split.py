# scripts/debug_split.py
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

def test():
    english_text = (
        "The provided context does not explicitly mention any rule number for \"short tenders\" or \"limited tendering\". "
        "However, it is mentioned that such tenders can be done without wide publicity in newspapers due to time constraints [Page 317]. "
        "Also, short-term / limited tenders are put on the website of the department as per Office Order No.98/ORD/1 dated 11th Feb., 2004 (applies to limited tenders also) [Clarification section].\n\n"
        "Regarding the process for such tenders, it is stated that they do not require publicity through newspapers and pre-qualified / known vendors are invited during the tender process. "
        "The details of terms can be obtained with the tender form from the concerned office within working days prior to the fixed date [Page 8].\n\n"
        "The contents of the Tender Document for any tendering method, including short or limited tenders, include sections such as Notice Inviting Tender (NIT), Instructions to Bidders (ITB), General Conditions of Contract (GCC), Special Conditions of Contract (SCC) and others [Page 317].\n\n"
        "The tender shall be submitted within the time table fixed in the online tender, and it will be opened as per that schedule. The tenders can be received by registered post or authorized courier [Page 9]."
    )

    llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="mashriram/sarvam-1",
        temperature=0.0,
        num_ctx=4096,
    )
    
    terms_str = "DSC, EMD, GFR, GeM, CRN, Rule, Section, Clause, Portal, PAN, GST, IFSC, PWD, L1"
    
    prompt = (
        "You are an expert English to Hindi translator. Translate the following English text into clean, high-quality Devanagari Hindi.\n\n"
        "Constraints:\n"
        "- Output ONLY the Hindi translation. Do NOT add any notes, comments, or explanations.\n"
        "- Preserve all original formatting: numbered lists (1. 2. 3.), bullet points (-), and line breaks exactly.\n"
        "- Keep all numbers as standard Arabic numerals (1, 2, 3) NOT Hindi numerals (१, २, ३).\n"
        "- Keep page/section references exactly as-is (e.g. [Page 5], [Section 4 Page 25], [Pages 14-16]).\n"
        f"- Keep key technical terms, codes, and abbreviations in English: {terms_str}.\n"
        "- NEVER mix English letters with Hindi letters inside a single word. (For example: use 'छत्तीसगढ़' instead of 'चhattीसगढ़').\n"
        "- Use ONLY proper Hindi Devanagari characters. Do NOT output characters from other scripts like Urdu (Arabic script) or Thai.\n\n"
        "Glossary of Preferred Translations:\n"
        "- 'tender' -> 'निविदा' or 'टेंडर' (NEVER use 'प्रस्ताव' or 'बोली' for tender)\n"
        "- 'limited tender' -> 'सीमित निविदा'\n"
        "- 'short tender' / 'short term tender' / 'short-term tender' -> 'अल्पकालीन निविदा' or 'शॉर्ट टेंडर'\n"
        "- 'bid' -> 'बोली' or 'निविदा'\n"
        "- 'bidder' -> 'बोलीदाता'\n"
        "- 'procurement' -> 'प्रोक्योरमेंट' or 'क्रय'\n"
        "- 'corrigendum' -> 'शुद्धिपत्र' or 'संशोधन'\n"
        "- 'GFR' -> 'जीएफआर'\n\n"
        f"Text to translate:\n{english_text}\n\n"
        "Hindi Translation:"
    )

    print("Invoking Ollama...")
    res = llm.invoke(prompt)
    print("Ollama response finished.")
    
    with open("scripts/raw_response.txt", "w", encoding="utf-8") as f:
        f.write(res)
    print("Raw response written to scripts/raw_response.txt")

if __name__ == "__main__":
    test()
