# scripts/test_sarvam_citation_preservation.py
import sys
import re
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_community.llms import Ollama
from app.core.config import settings

# Reconfigure stdout for utf-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def clean_sarvam_hindi(text: str) -> str:
    if not text:
        return text
        
    text = text.strip()
    
    # 1. Remove introductory prefixes (e.g. "हिंदी में अनुवादः ", "अनुवाद:", "Hindi:")
    for colon in [':', 'ः']:
        if colon in text:
            idx = text.find(colon)
            if idx < 30: # If it's near the beginning of the text
                text = text[idx+1:].strip()
                
    # 2. Strip surrounding quotes if model wrapped its translation
    # Strip double quotes
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    # Strip single quotes
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()
    # Strip Devanagari quotes
    if text.startswith('“') and text.endswith('”'):
        text = text[1:-1].strip()
        
    # 3. Convert Devanagari digits to standard Arabic digits
    devanagari_digits = "०१२३४५६७८९"
    arabic_digits = "0123456789"
    trans_table = str.maketrans(devanagari_digits, arabic_digits)
    text = text.translate(trans_table)
    
    # 4. Fix Marathi leaks and common errors
    marathi_replacements = {
        r'\bदेखील\b': 'भी',
        r'\bमर्यादित\b': 'सीमित',
        r'\bवर\b': 'पर',
        r'\bमध्ये\b': 'में',
        r'\bआहे\b': 'है',
        r'\bआहेत\b': 'हैं',
        r'\bकेले\b': 'किया',
        r'\bकेली\b': 'की',
        r'\bहोते\b': 'था',
        r'\bहोती\b': 'थी',
        r'\bतन्‍वारे\b': 'निविदा',
        r'\bनिविधा\b': 'निविदा',
        r'\bनिविध\b': 'निविद',
        r'\bबोलीदाता\b': 'निविदादाता',
        r'\bबोलीदाताओं\b': 'निविदादाताओं',
    }
    for pat, rep in marathi_replacements.items():
        text = re.sub(pat, rep, text)
        
    text = text.replace("</s>", "").strip()
    return text

def translate_with_citation_preservation(llm, text):
    # Split text into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    translated_paragraphs = []
    
    for p_idx, paragraph in enumerate(paragraphs):
        # Split paragraph into sentences
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        translated_sentences = []
        
        for s_idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Extract citations in square brackets
            citations = re.findall(r'(\[[^\]]+\])', sentence)
            
            # Remove citations to send clean text to model
            clean_sentence = sentence
            for cit in citations:
                clean_sentence = clean_sentence.replace(cit, "")
            
            # Normalize whitespace
            clean_sentence = re.sub(r'\s+', ' ', clean_sentence).strip()
            
            if not clean_sentence:
                translated_sentences.append(sentence)
                continue
                
            # Translate clean sentence
            prompt = f"Translate this English sentence to Hindi: \"{clean_sentence}\"\nHindi:"
            translated_s = llm.invoke(prompt).strip()
            
            # Clean up the output using python replacements
            translated_s = clean_sarvam_hindi(translated_s)
            
            # Append citations back to the translated sentence
            if citations:
                translated_s = translated_s.rstrip('.। ')
                cit_str = " " + " ".join(citations)
                translated_s = f"{translated_s}{cit_str}।"
            else:
                # Ensure it ends with standard Devanagari full stop (।)
                if not translated_s.endswith('।') and not translated_s.endswith('.'):
                    translated_s += '।'
                    
            translated_sentences.append(translated_s)
            
        translated_paragraphs.append(" ".join(translated_sentences))
        
    return "\n\n".join(translated_paragraphs)

def run_test():
    english_text = (
        "The provided context does not explicitly mention any rule number for \"short tenders\" or \"limited tendering\". "
        "However, it is mentioned that such tenders can be done without wide publicity in newspapers due to time constraints [Page 317]. "
        "Also, short-term / limited tenders are put on the website of the department as per Office Order No.98/ORD/1 dated 11th Feb., 2004 (applies to limited tenders also) [Clarification section].\n\n"
        "Regarding the process for such tenders, it is stated that they do not require publicity through newspapers and pre-qualified / known vendors are invited during the tender process. "
        "The details of terms can be obtained with the tender form from the concerned office within working days prior to the fixed date [Page 8].\n\n"
        "The contents of the Tender Document for any tendering method, including short or limited tenders, include sections such as Notice Inviting Tender (NIT), Instructions to Bidders (ITB), General Conditions of Contract (GCC), Special Conditions of Contract (SCC) and others [Page 317].\n\n"
        "The tender shall be submitted within the time table fixed in the online tender, and it will be opened as per that schedule. The tenders can be received by registered post or authorized courier [Page 9]."
    )

    print("Initializing Ollama for Sarvam...")
    llm = Ollama(
        base_url=settings.OLLAMA_BASE_URL,
        model="mashriram/sarvam-1",
        temperature=0.0,
        num_ctx=4096,
    )
    
    print("Translating with Citation Preservation...")
    t0 = time.time()
    final_output = translate_with_citation_preservation(llm, english_text)
    print(f"Total time taken: {time.time() - t0:.2f} seconds\n")
    
    print("--- FINAL TRANSLATED OUTPUT ---")
    print(final_output)
    print("-------------------------------")

if __name__ == "__main__":
    run_test()
