# scripts/test_split_translation.py
import sys
import re
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

def clean_translation(text: str) -> str:
    if not text:
        return text
    
    # 1. Convert Devanagari digits to Arabic digits
    devanagari_digits = "०१२३४५६७८९"
    arabic_digits = "0123456789"
    trans_table = str.maketrans(devanagari_digits, arabic_digits)
    text = text.translate(trans_table)
    
    # 2. Fix Marathi leaks (e.g., "देखील" -> "भी")
    text = re.sub(r'\bदेखील\b', 'भी', text)
    
    # 3. Clean trailing tokens
    text = text.replace("</s>", "").strip()
    
    return text

def translate_paragraph(llm, text: str) -> str:
    if not text.strip():
        return text
        
    terms_str = "DSC, EMD, GFR, GeM, CRN, Rule, Section, Clause, Portal, PAN, GST, IFSC, PWD, L1"
    
    prompt = (
        "You are an expert English to Hindi translator. Translate the following English paragraph into clean, high-quality Devanagari Hindi.\n\n"
        "Constraints:\n"
        "- Output ONLY the Hindi translation. Do NOT add any introduction, notes, comments, or explanations.\n"
        "- Use ONLY proper HINDI Devanagari words. Do NOT use Marathi words (such as 'देखील', 'वर', 'मध्ये', 'निविदा फॉर्ममधून', 'दस्तऐवजांच्या', 'यांचा', 'केलेल्या', 'झाले', 'केले'). Use standard Hindi equivalents (such as 'भी', 'पर', 'में', 'निविदा फॉर्म से', 'दस्तावेजों का', 'इनका', 'किए गए', 'हुआ', 'किया').\n"
        "- Keep all numbers as standard Arabic numerals (1, 2, 3) NOT Hindi numerals (१, २, ३).\n"
        "- Keep page/section references exactly as-is (e.g. [Page 5], [Section 4 Page 25], [Pages 14-16]).\n"
        f"- Keep key technical terms, codes, and abbreviations in English: {terms_str}.\n"
        "- NEVER mix English letters with Hindi letters inside a single word.\n"
        "- Use ONLY proper Hindi Devanagari characters.\n\n"
        f"Paragraph to translate:\n{text.strip()}\n\n"
        "Hindi Translation:"
    )
    
    res = llm.invoke(prompt).strip()
    return clean_translation(res)

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
        num_ctx=2048,
    )
    
    # Split by double newlines into paragraphs
    paragraphs = english_text.split("\n\n")
    print(f"Split text into {len(paragraphs)} paragraphs.")
    
    start_time = time.time()
    translated_paras = []
    for i, para in enumerate(paragraphs):
        print(f"Translating paragraph {i+1}/{len(paragraphs)}...")
        para_start = time.time()
        trans = translate_paragraph(llm, para)
        elapsed_para = time.time() - para_start
        print(f"Paragraph {i+1} took {elapsed_para:.2f} seconds.")
        translated_paras.append(trans)
        
    final_translation = "\n\n".join(translated_paras)
    total_elapsed = time.time() - start_time
    
    print(f"Total Time Taken: {total_elapsed:.2f} seconds")
    with open("scripts/split_output.txt", "w", encoding="utf-8") as f:
        f.write(final_translation)
    print("Translation written to scripts/split_output.txt")

if __name__ == "__main__":
    test()
