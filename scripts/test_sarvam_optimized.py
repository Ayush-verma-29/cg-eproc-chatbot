# scripts/test_sarvam_optimized.py
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
    
    # Remove metadata lines and prompt leakages
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        # Skip lines that look like prompt instructions or introductory phrases
        if any(skip in l for skip in ["Translate", "translation", "अनुवाद", "यहाँ", "मूल पाठ", "अंग्रेजी"]):
            continue
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Convert Devanagari digits to standard Arabic digits
    devanagari_digits = "०१२३४५६७८९"
    arabic_digits = "0123456789"
    trans_table = str.maketrans(devanagari_digits, arabic_digits)
    text = text.translate(trans_table)
    
    # Fix Marathi leaks and common errors
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
    }
    for pat, rep in marathi_replacements.items():
        text = re.sub(pat, rep, text)
        
    text = text.replace("</s>", "").strip()
    return text

def test_optimized():
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

    # Strategy 4: Few-shot translation prompt
    print("\n--- STRATEGY 4: Few-shot Prompt ---")
    few_shot_prompt = (
        "Translate the English text to Devanagari Hindi. Follow the examples.\n\n"
        "Example 1:\n"
        "English: Bidder registration requires PAN, GST and bank details [Page 5].\n"
        "Hindi: बोलीदाता पंजीकरण के लिए PAN, GST और बैंक विवरण आवश्यक हैं [Page 5].\n\n"
        "Example 2:\n"
        "English: The technical bids will be opened on 15th March at 11:00 AM.\n"
        "Hindi: तकनीकी बोलियां 15 मार्च को सुबह 11:00 बजे खोली जाएंगी।\n\n"
        f"English: {english_text}\n"
        "Hindi:"
    )
    t0 = time.time()
    res4 = llm.invoke(few_shot_prompt).strip()
    print(f"Time: {time.time() - t0:.2f}s")
    print(f"Raw Output:\n{res4}")
    print(f"Cleaned Output:\n{clean_sarvam_hindi(res4)}\n")

    # Strategy 5: Sentence-by-Sentence Translation
    print("--- STRATEGY 5: Sentence-by-Sentence Translation ---")
    # Split text into sentences using simple regex
    sentences = re.split(r'(?<=[.!?])\s+', english_text.replace('\n\n', ' \n\n '))
    
    t0 = time.time()
    translated_sentences = []
    for i, s in enumerate(sentences):
        s = s.strip()
        if not s:
            continue
        if s == '\n\n' or s == '\n':
            translated_sentences.append("\n\n")
            continue
            
        sentence_prompt = (
            "Translate this English sentence to Hindi: "
            f"\"{s}\"\n"
            "Hindi:"
        )
        s_trans = llm.invoke(sentence_prompt).strip()
        
        # Remove surrounding quotes from translation
        if s_trans.startswith('"') and s_trans.endswith('"'):
            s_trans = s_trans[1:-1].strip()
        if s_trans.startswith("'") and s_trans.endswith("'"):
            s_trans = s_trans[1:-1].strip()
            
        s_clean = clean_sarvam_hindi(s_trans)
        translated_sentences.append(s_clean)
        print(f"Sentence {i+1} Translated: {s_clean[:40]}...")
        
    full_sentence_translation = " ".join(translated_sentences)
    # Clean up spacing around newlines
    full_sentence_translation = re.sub(r'\s*\n\n\s*', '\n\n', full_sentence_translation)
    print(f"Total Time: {time.time() - t0:.2f}s")
    print(f"Full Sentence-by-Sentence Output:\n{full_sentence_translation}\n")

if __name__ == "__main__":
    test_optimized()
