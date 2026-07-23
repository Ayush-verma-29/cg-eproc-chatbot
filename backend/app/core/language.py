# backend/app/core/language.py
import re
import time
from typing import List
from deep_translator import GoogleTranslator
from langdetect import detect

HINDI_RANGE = re.compile(r'[\u0900-\u097F]')
STRONG_HINGLISH_WORDS = re.compile(
    r'\b(?:kya|hain|ke|liye|hona|chahiye|fayde|fayda|milega|milte|kab|kaise|nhi|nahi|sakte|mujhe|kharidna|kharidne|kharid|batao|batayein|dekho|kare|karna|karo|gaya|gaye|rha|raha|rhi|rahi|apna|apne|mera|meri|hum|humein)\b',
    re.IGNORECASE
)
WEAK_HINGLISH_WORDS = re.compile(
    r'\b(?:lakh|lakhs|ko|hai|tak|kon|kis)\b',
    re.IGNORECASE
)
HINGLISH_WORDS = STRONG_HINGLISH_WORDS

class LanguageService:
    @staticmethod
    def is_hindi(text: str) -> bool:
        """Check if text contains Hindi characters or Hinglish patterns"""
        if HINDI_RANGE.search(text):
            return True
        if STRONG_HINGLISH_WORDS.search(text):
            return True
        if text.isascii():
            return False
        try:
            # Check with langdetect offline detection
            lang = detect(text)
            if lang in ['hi', 'mr', 'ne']:
                return True
        except:
            pass
        return False

    @staticmethod
    def is_hindi_document(text: str, threshold: float = 0.15) -> bool:
        """Check density of Devanagari characters in text to distinguish Hindi documents from English documents."""
        if not text:
            return False
        # Count Devanagari characters
        devanagari_chars = HINDI_RANGE.findall(text)
        all_letters = re.findall(r'[a-zA-Z\u0900-\u097F]', text)
        if not all_letters:
            return False
        ratio = len(devanagari_chars) / len(all_letters)
        # Real Hindi docs usually have >30%; use higher threshold for English-named files
        return ratio >= threshold

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect if text is Hindi (including Hinglish) or English, respecting explicit user instructions."""
        text_lower = text.lower()
        
        # Check if user requests English response
        english_request_patterns = [
            r'\bin\s+english\b',
            r'\benglish\s*(?:me|mein|main|mein|maii?n)\b',
            r'\benglish\s*(?:please|plz|only)\b',
            r'\b(?:reply|answer|respond|write|tell|explain)\s+(?:in\s+)?english\b',
            r'english\s*(?:में|मे|में\s*बताओ|में\s*बताएं|में\s*उत्तर|में\s*जवाब)',
            r'(?:इंग्लिश|अंग्रेजी|अंग्रेज़ी|अंगरेजी)\s*(?:में|मे|में\s*बताओ|में\s*बताएं|में\s*उत्तर|में\s*जवाब)'
        ]
        if any(re.search(pat, text_lower) for pat in english_request_patterns):
            return 'en'
            
        # Check if user requests Hinglish response
        hinglish_request_patterns = [
            r'\bin\s+hinglish\b',
            r'\bhinglish\s*(?:me|mein|main|mein|maii?n)\b',
            r'\bhinglish\s*(?:please|plz|only)\b',
            r'\b(?:reply|answer|respond|write|tell|explain)\s+(?:in\s+)?hinglish\b',
            r'hinglish\s*(?:में|मे|में\s*बताओ|में\s*बताएं|में\s*उत्तर|में\s*जवाब)'
        ]
        if any(re.search(pat, text_lower) for pat in hinglish_request_patterns):
            return 'hi-Latn'
            
        # Check if user requests Hindi response
        hindi_request_patterns = [
            r'\bin\s+hindi\b',
            r'\bhindi\s*(?:me|mein|main|mein|maii?n)\b',
            r'\bhindi\s*(?:please|plz|only)\b',
            r'\b(?:reply|answer|respond|write|tell|explain)\s+(?:in\s+)?hindi\b',
            r'hindi\s*(?:में|मे|में\s*बताओ|में\s*बताएं|में\s*उत्तर|में\s*जवाब)'
        ]
        if any(re.search(pat, text_lower) for pat in hindi_request_patterns):
            return 'hi'
            
        if LanguageService.is_hindi(text):
            # If query has Hinglish patterns but contains NO Devanagari Hindi characters, detect as Hinglish
            if not HINDI_RANGE.search(text) and HINGLISH_WORDS.search(text):
                return 'hi-Latn'
            return 'hi'
        return 'en'
    
    @staticmethod
    def translate_to_english(text: str) -> str:
        """Translate Hindi/Hinglish to English using Google Translate with retries"""
        if not text or not text.strip():
            return text

        try:
            from app.services.admin_config_service import admin_config_service
            config = admin_config_service.get_config()
            if not config.get("translation_enabled", True):
                return text
        except Exception:
            config = {}
            
        if not LanguageService.is_hindi(text):
            return text
            
        translated_text = None
        
        # Check if the query is written in Latin script (ASCII) but detected as Hinglish.
        # Google Translate's auto-detect will horribly fail on this, so we bypass it directly to local LLM.
        is_latin_hinglish = not HINDI_RANGE.search(text) and LanguageService.is_hindi(text)
        
        if not is_latin_hinglish and not getattr(LanguageService, "_offline_mode", False):
            for attempt in range(3):
                try:
                    translation = GoogleTranslator(source='auto', target='en').translate(text)
                    if translation:
                        translated_text = translation
                        break
                except Exception as e:
                    err_str = str(e)
                    if any(err in err_str for err in ["getaddrinfo failed", "unreachable host", "10065", "11001", "10060", "10054", "10061", "timed out", "timeout", "connection"]):
                        print("   [Network/timeout error detected. Bypassing further Google Translate attempts.]")
                        LanguageService._offline_mode = True
                        break
                        
                    print(f"   [Attempt {attempt+1}/3] Translation to English failed: {e}")
                    time.sleep(1 + attempt)
                    
        if translated_text is None or translated_text == text:
            # Fall back to local Ollama translation
            try:
                from langchain_community.llms import Ollama
                from app.core.config import settings
                # Use the main chatbot model (much more capable) for Latin Hinglish, fallback to translation model for others
                target_model = settings.LLM_MODEL if is_latin_hinglish else settings.TRANSLATION_MODEL
                print(f"   [Translating using local model {target_model} for Hindi/Hinglish query translation...]")
                local_translator = Ollama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=target_model,
                    temperature=0,
                    num_ctx=1024,
                    timeout=30
                )
                prompt = (
                    "You are a professional Hindi to English translator specializing in government procurement.\n"
                    "Translate the following Hindi or Hinglish query into clean, natural English.\n\n"
                    "Glossary of Preferred Translations:\n"
                    "- 'दो-बोली प्रणाली' / 'दो-बोली' -> 'two-bid system'\n"
                    "- 'बोली' -> 'bid'\n"
                    "- 'बोलीदाता' -> 'bidder'\n"
                    "- 'निविदा' -> 'tender'\n"
                    "- 'प्रदर्शन प्रतिभूति' / 'प्रदर्शन सुरक्षा' -> 'performance security'\n"
                    "- 'बयाना राशि' / 'ईएमडी' -> 'EMD' / 'bid security'\n\n"
                    "Constraints:\n"
                    "- Output ONLY the English translation. Do NOT add any notes, explanations, or quotes.\n\n"
                    f"Query: {text}\n\n"
                    "English Translation:"
                )
                res = local_translator.invoke(prompt).strip()
                for sep in ["English Translation:", "Translation:", "Note:", "Query:"]:
                    if sep in res:
                        res = res.split(sep)[-1].strip()
                # Remove wrapping quotes
                if res.startswith('"') and res.endswith('"'):
                    res = res[1:-1].strip()
                if res.startswith("'") and res.endswith("'"):
                    res = res[1:-1].strip()
                if res and res != text:
                    # Defense-in-depth: Reject translation if local LLM returned safety/refusal phrases
                    refusal_keywords = ["cannot", "sorry", "apologize", "illegal", "violate", "safety", "guideline", "ethics", "unethical"]
                    res_lower = res.lower()
                    if any(kw in res_lower for kw in refusal_keywords):
                        print(f"   [Local translator returned safety refusal. Discarding translation: {res}]")
                    else:
                        translated_text = res
            except Exception as ex:
                print(f"   [Ollama fallback query translation failed: {ex}]")

        if translated_text is None:
            translated_text = text
            
        # Post-processing to restore critical abbreviations if lost in translation
        mappings = {
            "emd": [r"\bemd\b", r"ईएमडी", r"earnest money", r"bid security"],
            "gfr": [r"\bgfr\b", r"जीएफआर", r"जी\.एफ\.आर\.", r"general financial rules"],
            "gem": [r"\bgem\b", r"जेम", r"government e-marketplace"],
            "msme": [r"\bmsme\b", r"\bmse\b", r"एमएसएमई", r"एमएसएमइ", r"micro,? small and medium"],
            "cvc": [r"\bcvc\b", r"सीवीसी", r"central vigilance commission"],
            "l1": [r"\bl1\b", r"\bl-1\b", r"एल१", r"एल1"],
            "pqc": [r"\bpqc\b", r"पीक्यूसी", r"pre-qualification criteria"],
            "dsc": [r"\bdsc\b", r"डीएससी", r"digital signature"]
        }
        
        restored = []
        for ab, patterns in mappings.items():
            has_in_orig = False
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE):
                    has_in_orig = True
                    break
                    
            if has_in_orig:
                eng_patterns = [patterns[0]]
                if len(patterns) > 2:
                    eng_patterns.extend(patterns[2:])
                    
                has_in_trans = False
                for pat in eng_patterns:
                    if re.search(pat, translated_text, re.IGNORECASE):
                        has_in_trans = True
                        break
                        
                if not has_in_trans:
                    restored.append(ab.upper())

        # Dynamic config protected terms check
        try:
            protected_terms = config.get("protected_terms", [])
        except Exception:
            protected_terms = []

        for term in protected_terms:
            term_upper = term.upper()
            if term_upper not in restored:
                pattern = r"\b" + re.escape(term) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    if not re.search(pattern, translated_text, re.IGNORECASE):
                        restored.append(term_upper)
                    
        if restored:
            translated_text = f"{translated_text} ({', '.join(restored)})"
            
        return translated_text
    
    @staticmethod
    def _is_valid_hindi_output(original: str, translated: str) -> bool:
        """Check if translated output is valid Hindi (not garbage/hallucination)"""
        if not translated or not translated.strip():
            return False
        # Count Devanagari characters in output
        deva_count = len(HINDI_RANGE.findall(translated))
        all_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', translated))
        if all_alpha == 0:
            return False
        # Require at least 25% Devanagari characters in translation of English text
        deva_ratio = deva_count / all_alpha
        if deva_ratio < 0.25:
            print(f"   [Translation quality too low ({deva_ratio:.0%} Devanagari) - falling back to English]")
            return False
        # Detect obvious hallucination patterns
        hallucination_patterns = [
            r'mysql>', r'select \*', r'INSERT INTO', r'DROP TABLE',  # SQL hallucination
            r'<\|im_start\|>', r'<\|im_end\|>',                      # Leaked prompt tokens
            r'\[INST\]', r'\[/INST\]',                                # Leaked Mistral tokens
            r'User:', r'Assistant:', r'Human:',                       # Role-play leak
            r'[\u4e00-\u9fff]',                                       # Chinese characters leaking
        ]
        for pat in hallucination_patterns:
            if re.search(pat, translated, re.IGNORECASE):
                print(f"   [Hallucination detected in translation (pattern: {pat[:20]}) - falling back to English]")
                return False
        return True

    @staticmethod
    def clean_translated_hindi(text: str) -> str:
        """Clean translated Hindi text to fix mixed script, foreign scripts, and minor translation glitches from llama"""
        if not text:
            return text
        
        # 1. Fix mixed English/Hindi transliteration of Chhattisgarh
        text = re.sub(r'\b(?:c[hH]+|च)[a-zA-Z\u0900-\u097F]*[ीस]\s*[गग]ढ़\b', 'छत्तीसगढ़', text)
        text = re.sub(r'\b(?:c[hH]+|च)[a-zA-Z\u0900-\u097F]*[ीस]\s*[गग]ढ़\b', 'छत्तीसगढ़', text)
        text = text.replace('चhattीसगढ़', 'छत्तीसगढ़')
        text = text.replace('चhattीसगढ़', 'छत्तीसगढ़')
        
        # 1c. Fix translation/transliteration distortions of Chhattisgarh (e.g. चतरा, चॕट्गॊड़, चॕट्‍टिस्‍गड़रह्ण)
        text = re.sub(r'\bचतरा\b', 'छत्तीसगढ़', text)
        text = re.sub(u'\\bच\\u0955[\\u0900-\\u097F\\u200c\\u200d]*', 'छत्तीसगढ़', text)
        text = text.replace("चतरा ", "छत्तीसगढ़ ")
        text = text.replace("चतराई-प्रोक्योरमेंट", "छत्तीसगढ़ ई-प्रोक्योरमेंट")
        
        # 1d. Fix translation/transliteration distortions of e-Procurement (e.g. ईप्रोक्यूड़रड़ल)
        text = text.replace("ईप्रोक्यूड़रड़ल", "ई-प्रोक्योरमेंट")
        
        # 1e. Fix translation/transliteration distortions of L1 (e.g. पर्ग-1, पर्ग प्रथम -> L1)
        text = text.replace("पर्ग-1", "L1")
        text = text.replace("पर्ग प्रथम", "L1")
        text = text.replace("पर्ग 1", "L1")
        text = text.replace("पर्ग", "L1")
        
        # 1f. Fix translation/transliteration distortions of CRN (e.g. क्रोन -> सीआरएन)
        text = text.replace("क्रोन (क्रोन)", "सीआरएन (CRN)")
        text = text.replace("क्रोन (सीआरएन)", "सीआरएन (CRN)")
        text = text.replace("क्रोन", "सीआरएन")
        
        # Fix double punctuation from translation combining visarga/colon and danda
        text = text.replace("ः।", "ः")
        text = text.replace(":।", ":")
        text = text.replace("।ः", "ः")
        text = text.replace("।:", ":")
        
        # NOTE: Do NOT strip REF/रेफ़ placeholders here — link restoration runs AFTER this function.
        
        # 1b. Fix "Chhattisgarh Financial Rules" translated to Hindi (e.g. छत्तीसगढ़ वित्तीय नियम -> सामान्य वित्तीय नियम (जीएफआर))
        text = re.sub(r'छत्तीसगढ़\s+(?:के\s+)?वित्तीय\s+नियम', 'सामान्य वित्तीय नियम (जीएफआर)', text)
        
        # 2. Fix Thai "ของ" (of) leaking into Hindi
        text = re.sub(r'\s*ของ\s*', ' की ', text)
        
        # 3. Map Arabic/Urdu characters to Devanagari equivalents if they are mixed in
        char_map = {
            '\u0631': '\u0930',  # reh -> र
            '\u06cc': '\u0940',  # Urdu yeh -> ी
            '\u064a': '\u0940',  # Arabic yeh -> ी
            '\u0649': '\u0940',  # alef maksura -> ी
            '\u062c': '\u091c',  # jim -> ज
            '\u0645': '\u092e',  # meem -> म
            '\u0627': '\u093e',  # alif -> ा
            '\u062f': '\u0926',  # dal -> द
            '\u0628': '\u092c',  # beh -> ब
            '\u062a': '\u0924',  # teh -> त
            '\u0646': '\u0928',  # noon -> न
            '\u06a9': '\u0915',  # Persian kaf -> क
            '\u0643': '\u0915',  # Arabic kaf -> क
            '\u0634': '\u0936',  # sheen -> श
            '\u06c1': '\u0939',  # Urdu heh -> ह
            '\u06be': '\u0939',  # Arabic heh -> ह
            '\u0648': '\u0935',  # waw -> व
        }
        
        for arabic_char, hindi_char in char_map.items():
            text = text.replace(arabic_char, hindi_char)
            
        # 4. Convert Devanagari digits to standard Arabic digits
        devanagari_digits = "०१२३४५६७८९"
        arabic_digits = "0123456789"
        trans_table = str.maketrans(devanagari_digits, arabic_digits)
        text = text.translate(trans_table)

        # 5. Fix Marathi leaks
        text = re.sub(r'\bदेखील\b', 'भी', text)
        text = re.sub(r'\bमर्यादित\b', 'सीमित', text)
        text = re.sub(r'\bवर\b', 'पर', text)
        text = re.sub(r'\bमध्ये\b', 'में', text)
        text = re.sub(r'\bआहे\b', 'है', text)
        text = re.sub(r'\bआहेत\b', 'हैं', text)
        text = re.sub(r'\bकेले\b', 'किया', text)
        text = re.sub(r'\bकेली\b', 'की', text)
        text = re.sub(r'\bहोते\b', 'था', text)
        text = re.sub(r'\bहोती\b', 'थी', text)
        text = text.replace("मर्यादित निविदा", "सीमित निविदा")
        
        # Additional Marathi word mappings
        marathi_map = {
            'पर्यंत': 'तक',
            'किंवा': 'या',
            'सर्व': 'सभी',
            'कामगिरी': 'प्रदर्शन',
            'सुरक्षेचा': 'सुरक्षा का',
            'असावा': 'होना चाहिए',
            'असावे': 'होनी चाहिए',
            'झाले': 'हुआ',
            'झाली': 'हुई',
            'करण्यात': 'करने',
            'येईल': 'जाएगा',
            'येणार': 'आने',
            'यावे': 'चाहिए',
            'नाही': 'नहीं',
            'आणि': 'और',
            'त्यानुसार': 'तदनुसार',
            'करारांमध्ये': 'अनुबंधों में',
            'बोलींमध्ये': 'बोलियों में',
            'संपलेल्या': 'समाप्त होने वाले',
            'कमी': 'कम',
            'करून': 'करके',
            'सादर': 'प्रस्तुत',
            'केल्यास': 'करने पर',
            'येतील': 'जाएंगे',
            'आवश्यकता\s+नाही': 'आवश्यकता नहीं है',
        }
        for pat, rep in marathi_map.items():
            text = re.sub(pat, rep, text)
            
        text = re.sub(r'सादर\s+करण्यात\s+येईल', 'प्रस्तुत किया जाएगा', text)
        text = re.sub(r'सादर\s+करावे', 'प्रस्तुत करना चाहिए', text)

        # 5b. Clean translation meta-prompts and announcements
        text = re.sub(r'इस\s+अंग्रेजी\s+पाठ\s+(?:को|का)\s+हिंदी\s+में\s+अनुवाद\s+(?:करें|कीजिए|है)[ः:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'इस\s+पाठ\s+(?:को|का)\s+हिंदी\s+में\s+अनुवाद\s+(?:करें|कीजिए|है)[ः:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'इस\s+अंग्रेजी\s+पाठ\s+का\s+(?:हिंदी\s+)?अनुवाद[ः:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'यह\s+हिंदी\s+में\s+अनुवादित\s+है[ः:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'का\s+अनुवाद\s+हिंदी\s+में\s+(?:है|किया\s+गया\s+है)[ः:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'को\s+हिंदी\s+में\s+["\'“‘][^"\'”’]+["\'”’]\s+के\s+रूप\s+में\s+अनुवादित\s+किया\s+जा\s+सकता\s+है', '', text, flags=re.IGNORECASE)
        text = re.sub(r'को\s+हिंदी\s+में\s+[^"\',।]+\s+के\s+रूप\s+में\s+अनुवादित\s+किया\s+जा\s+सकता\s+है', '', text, flags=re.IGNORECASE)
        text = re.sub(r'हिंदी\s+(?:में\s+)?अनुवाद\s*[:ः\s]*', '', text, flags=re.IGNORECASE)
        
        # 5c. Correct common translation hallucinations/errors
        # Correct Rule 165 late bids hallucination in Hindi
        text = re.sub(
            r'देर\s+से\s+(?:प्राप्त|की\s+गई|जमा\s+की\s+गई)\s+बोलियों?\s+(?:को\s+)?निर्दिष्ट\s+(?:तिथि|तारीख)\s+और\s+समय\s+के\s+बाद\s+(?:स्वीकार\s+किया|माना)\s+जा\s+सकता\s+है',
            'देर से प्राप्त बोलियों पर विचार नहीं किया जाना चाहिए (नियम 165)',
            text
        )
        
        # Correct performance security exemption limit in Hindi (1 lakh limit)
        text = re.sub(
            r'एक\s+लाख\s+रुपये\s+से\s+अधिक\s+(?:मूल्य\s+)?के\s+(?:अनुबंधों|करारों)\s+(?:के\s+लिए\s+)?प्रदर्शन\s+(?:सुरक्षा|प्रतिभूति)\s+(?:जमा\s+करने\s+|प्रदान\s+करने\s+)?की\s+आवश्यकता\s+नहीं\s+है',
            'एक लाख रुपये तक के अनुबंधों के लिए प्रदर्शन सुरक्षा जमा करने की आवश्यकता नहीं है',
            text
        )
        
        # Clean double/trailing quotes if they were left over
        text = re.sub(r'^[“"\'\s]+', '', text)
        text = re.sub(r'[”"\'\s]+$', '', text)
        
        # Clean multiple spaces
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 6. Fix common spelling errors from Llama (e.g., "निविधा" -> "निविदा")
        text = text.replace("निविधा", "निविदा")
        text = text.replace("निविध", "निविद")
        
        # 7. Strip trailing model end tokens
        text = text.replace("</s>", "")
            
        return text

    @staticmethod
    def clean_sarvam_hindi_output(text: str) -> str:
        """Specific cleanup for small bilingual models like Sarvam-1"""
        if not text:
            return text
            
        text = text.strip()
        # Strip trailing model end tokens first
        text = text.replace("</s>", "").strip()
        
        # 1. Remove introductory prefixes (e.g. "हिंदी में अनुवादः ", "अनुवाद:", "Hindi:", and full sentence prompts)
        prefixes = [
            r"^इस अंग्रेजी पाठ का हिंदी में अनुवाद\s*है\s*:",
            r"^इस अंग्रेजी पाठ का हिंदी में अनुवाद\s*:",
            r"^इस अंग्रेजी पाठ का हिंदी में अनुवाद",
            r"^इस पाठ का हिंदी में अनुवाद\s*:",
            r"^इस पाठ का हिंदी में अनुवाद",
            r"^हिंदी में अनुवाद\s*(करें|कीजिए)?\s*[ः:]?",
            r"^हिंदी में अनुवादः",
            r"^हिंदी में अनुवाद:",
            r"^अनुवाद:",
            r"^Hindi:"
        ]
        for pattern in prefixes:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
            
        # Remove introductory sentences that end with "अनुवाद:" or similar
        # e.g., "तकनीकी रूप से जटिल आवश्यकताओं के लिए अनुवादः" or "यहाँ अनुवाद है:"
        text = re.sub(r'^[^।\n]+?(?:के\s+लिए|का)\s+(?:हिंदी\s+)?अनुवाद\s*[ः:]?\s*["\'“‘]?', '', text).strip()
        text = re.sub(r'^(?:यहाँ|यहां|यह)\s+(?:का\s+)?(?:हिंदी\s+)?अनुवाद\s+(?:है|किया\s+गया\s+है)\s*[ः:]?\s*["\'“‘]?', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'^अनुवाद\s*[:ः\s]*["\'“‘]?', '', text, flags=re.IGNORECASE).strip()

        # Clean inline/leaked model announcements and translation prompts globally
        text = re.sub(r'हिंदी\s+में\s+किया\s+गया\s+है\s*[ः:]?\s*["\'“‘]?', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'अनुवाद\s+(?:करें|कीजिए|करके|होगा|है|किया\s+गया\s+है)\s*[,，]?\s*["\'“‘]?', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'(?:हिंदी\s+में\s+)?अनुवाद\s*[:ः\s]*["\'“‘]?', '', text, flags=re.IGNORECASE).strip()

        # Strip remaining colons or punctuation if left at start
        text = re.sub(r'^[:ः\s]+', '', text).strip()
                    
        # 2. Strip surrounding/unbalanced quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
        elif text.startswith('"') and not text.endswith('"'):
            text = text[1:].strip()
        elif text.endswith('"') and not text.startswith('"'):
            text = text[:-1].strip()

        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1].strip()
        elif text.startswith("'") and not text.endswith("'"):
            text = text[1:].strip()
        elif text.endswith("'") and not text.startswith("'"):
            text = text[:-1].strip()

        if text.startswith('“') and text.endswith('”'):
            text = text[1:-1].strip()
        elif text.startswith('“') and not text.endswith('”'):
            text = text[1:].strip()
        elif text.endswith('”') and not text.startswith('“'):
            text = text[:-1].strip()
            
        # Clean unbalanced trailing quotes if we stripped the opening quote earlier
        if not text.startswith('"') and text.endswith('"'):
            text = text[:-1].strip()
        if not text.startswith('“') and text.endswith('”'):
            text = text[:-1].strip()
        if not text.startswith("'") and text.endswith("'"):
            text = text[:-1].strip()
            
        return text

    @staticmethod
    def translate_to_hindi(text: str) -> str:
        """Translate English to Hindi using Google Translate with local Ollama fallback"""
        if not text or not text.strip():
            return text

        try:
            from app.services.admin_config_service import admin_config_service
            config = admin_config_service.get_config()
            if not config.get("translation_enabled", True):
                return text
        except Exception:
            config = {}

        translated_text = None

        # Try Google Translate first if not offline
        if not getattr(LanguageService, "_offline_mode", False):
            for attempt in range(3):
                try:
                    translation = GoogleTranslator(source='auto', target='hi').translate(text)
                    if translation:
                        translated_text = translation
                        break
                except Exception as e:
                    err_str = str(e)
                    if any(err in err_str for err in ["getaddrinfo failed", "unreachable host", "10065", "11001", "10060", "10054", "10061", "timed out", "timeout", "connection"]):
                        print("   [Network/timeout error detected. Bypassing further Google Translate attempts.]")
                        LanguageService._offline_mode = True
                        break
                    print(f"   [Attempt {attempt+1}/3] Translation to Hindi failed: {e}")
                    time.sleep(1 + attempt)

        if translated_text is not None and translated_text != text:
            cleaned_text = LanguageService.clean_translated_hindi(translated_text)
            if LanguageService._is_valid_hindi_output(text, cleaned_text):
                return cleaned_text

        # Fall back to local Ollama translation
        try:
            from langchain_community.llms import Ollama
            from app.core.config import settings

            print(f"   [Translating English response to Hindi using local model {settings.TRANSLATION_MODEL}...]")
            local_translator = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.TRANSLATION_MODEL,
                temperature=0,
                num_ctx=4096,          # Full response context — we send the whole English answer at once
                repeat_penalty=1.1,
                timeout=120,           # Longer timeout for full-response translation
            )

            # Check if model is Sarvam and use optimized structured line-by-line pipeline
            if "sarvam" in settings.TRANSLATION_MODEL.lower():
                print("   [Using optimized structured line-by-line pipeline for Sarvam...]")
                
                # Patterns for regex matching list numbering and bold headers
                pattern_bold = re.compile(
                    r'^\s*(?:(\d+\.|\*|-|[a-zA-Z]\.)\s*)?\*\*([^*]+)\*\*\s*(:|-)?\s*(.*)$',
                    re.DOTALL
                )
                pattern_list = re.compile(
                    r'^\s*(\d+\.|\*|-|[a-zA-Z]\.)\s*(.*)$',
                    re.DOTALL
                )

                lines = text.split("\n")
                translated_lines = []

                for line in lines:
                    stripped_line = line.strip()
                    if not stripped_line:
                        translated_lines.append("")
                        continue

                    # Extract markdown links and URLs using REF placeholders to prevent translation mangling
                    links = []
                    def repl_link(match):
                        links.append(match.group(0))
                        return f"REF{len(links)-1}"
                    
                    # Match markdown links [label](url)
                    clean_line = re.sub(r'(\[[^\]]+\]\([^)]+\))', repl_link, line)
                    # Match absolute file links or web URLs
                    clean_line = re.sub(r'(\bfile:///[\S]+|\bhttps?://[\S]+)', repl_link, clean_line)

                    # Extract citations
                    citations = re.findall(r'(\[[^\]]+\])', clean_line)
                    for cit in citations:
                        clean_line = clean_line.replace(cit, "")
                    clean_line = re.sub(r'\s+', ' ', clean_line).strip()

                    if not clean_line:
                        # Restore links on the original line if clean_line was empty
                        reconstructed = line
                        for link_idx, orig_link in enumerate(links):
                            pattern = re.compile(rf'(?:REF|रेफ़|रेफ)\s*{link_idx}', re.IGNORECASE)
                            if pattern.search(reconstructed):
                                reconstructed = pattern.sub(orig_link, reconstructed)
                            else:
                                reconstructed = reconstructed.replace(f"REF{link_idx}", orig_link)
                        translated_lines.append(reconstructed)
                        continue

                    # Try matching bold title with optional list marker
                    match_bold = pattern_bold.match(clean_line)
                    if match_bold:
                        marker = match_bold.group(1) or ""
                        bold_title = match_bold.group(2) or ""
                        separator = match_bold.group(3) or ":"
                        remaining_text = match_bold.group(4) or ""

                        # Translate bold title
                        trans_title = ""
                        if bold_title.strip():
                            prompt_title = f"Translate this English phrase to Hindi: \"{bold_title.strip()}\"\nHindi:"
                            res_title = local_translator.invoke(prompt_title).strip()
                            trans_title = LanguageService.clean_sarvam_hindi_output(res_title)
                            trans_title = LanguageService.clean_translated_hindi(trans_title)
                        
                        # Translate remaining text
                        trans_remaining = ""
                        if remaining_text.strip():
                            prompt_rem = f"Translate this English text to Hindi: \"{remaining_text.strip()}\"\nHindi:"
                            res_rem = local_translator.invoke(prompt_rem).strip()
                            trans_remaining = LanguageService.clean_sarvam_hindi_output(res_rem)
                            trans_remaining = LanguageService.clean_translated_hindi(trans_remaining)

                        # Reconstruct
                        marker_part = f"{marker} " if marker else ""
                        separator_part = f"{separator} " if separator else " "
                        reconstructed = f"{marker_part}**{trans_title}**{separator_part}{trans_remaining}"
                        
                        # Append citations back
                        if citations:
                            reconstructed = reconstructed.rstrip('.। ')
                            cit_str = " " + " ".join(citations)
                            reconstructed = f"{reconstructed}{cit_str}।"
                        else:
                            if reconstructed.strip() and not reconstructed.endswith('।') and not reconstructed.endswith('.'):
                                reconstructed += '।'
                                
                        # Restore links
                        for link_idx, orig_link in enumerate(links):
                            pattern = re.compile(rf'(?:REF|रेफ़|रेफ)\s*{link_idx}', re.IGNORECASE)
                            if pattern.search(reconstructed):
                                reconstructed = pattern.sub(orig_link, reconstructed)
                            else:
                                reconstructed = reconstructed.replace(f"REF{link_idx}", orig_link)
                                
                        translated_lines.append(reconstructed)
                        continue

                    # Try matching list marker only
                    match_list = pattern_list.match(clean_line)
                    if match_list:
                        marker = match_list.group(1) or ""
                        remaining_text = match_list.group(2) or ""

                        # Translate remaining text
                        trans_remaining = ""
                        if remaining_text.strip():
                            prompt_rem = f"Translate this English text to Hindi: \"{remaining_text.strip()}\"\nHindi:"
                            res_rem = local_translator.invoke(prompt_rem).strip()
                            trans_remaining = LanguageService.clean_sarvam_hindi_output(res_rem)
                            trans_remaining = LanguageService.clean_translated_hindi(trans_remaining)

                        # Reconstruct
                        marker_part = f"{marker} " if marker else ""
                        reconstructed = f"{marker_part}{trans_remaining}"

                        # Append citations back
                        if citations:
                            reconstructed = reconstructed.rstrip('.। ')
                            cit_str = " " + " ".join(citations)
                            reconstructed = f"{reconstructed}{cit_str}।"
                        else:
                            if reconstructed.strip() and not reconstructed.endswith('।') and not reconstructed.endswith('.'):
                                reconstructed += '। '

                        # Restore links
                        for link_idx, orig_link in enumerate(links):
                            pattern = re.compile(rf'(?:REF|रेफ़|रेफ)\s*{link_idx}', re.IGNORECASE)
                            if pattern.search(reconstructed):
                                reconstructed = pattern.sub(orig_link, reconstructed)
                            else:
                                reconstructed = reconstructed.replace(f"REF{link_idx}", orig_link)

                        translated_lines.append(reconstructed)
                        continue

                    # Standard translation fallback
                    prompt = f"Translate this English text to Hindi: \"{clean_line}\"\nHindi:"
                    res = local_translator.invoke(prompt).strip()
                    cleaned = LanguageService.clean_sarvam_hindi_output(res)
                    cleaned = LanguageService.clean_translated_hindi(cleaned)

                    # Append citations back
                    if citations:
                        cleaned = cleaned.rstrip('.। ')
                        cit_str = " " + " ".join(citations)
                        cleaned = f"{cleaned}{cit_str}।"
                    else:
                        if cleaned.strip() and not cleaned.endswith('।') and not cleaned.endswith('.'):
                            cleaned += '। '

                    # Restore links
                    for link_idx, orig_link in enumerate(links):
                        pattern = re.compile(rf'(?:REF|रेफ़|रेफ)\s*{link_idx}', re.IGNORECASE)
                        if pattern.search(cleaned):
                            cleaned = pattern.sub(orig_link, cleaned)
                        else:
                            cleaned = cleaned.replace(f"REF{link_idx}", orig_link)

                    translated_lines.append(cleaned)

                final_translation = "\n".join(translated_lines)
                
                # Safety sweep: strip any REF/रेफ़ placeholders that restoration couldn't resolve
                # (happens when Sarvam transliterates REF in a way not caught by the patterns)
                final_translation = re.sub(r'(?:REF|रेफ़|रेफ)\s*\d+', '', final_translation)
                final_translation = re.sub(r'\s{2,}', ' ', final_translation).strip()
                
                if not LanguageService._is_valid_hindi_output(text, final_translation):
                    return text
                return final_translation

            # Otherwise use default translation method for Llama/Qwen
            protected_terms = config.get("protected_terms", [])
            terms_str = ", ".join(protected_terms) if protected_terms else "DSC, EMD, GFR, GeM, CRN, Rule, Section, Clause, Portal, PAN, GST, IFSC, PWD, L1"

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
                "- 'vendor' / 'vendors' -> 'विक्रेता' or 'आपूर्तिकर्ता' (NEVER use 'भंडारणकर्ता' or 'स्टोरकीपर' for vendor)\n"
                "- 'limited' -> 'सीमित' (NEVER use 'मर्यादित' for limited)\n"
                "- 'time constraints' / 'urgency' -> 'समय की कमी' or 'समय सीमा'\n"
                "- 'procurement' -> 'प्रोक्योरमेंट' or 'क्रय'\n"
                "- 'corrigendum' -> 'शुद्धिपत्र' or 'संशोधन'\n"
                "- 'GFR' -> 'जीएफआर'\n\n"
                f"Text to translate:\n{text}\n\n"
                "Hindi Translation:"
            )

            translated_text = local_translator.invoke(prompt).strip()

            # Strip leaked prompt tokens and notes
            for sep in ["<|im_end|>", "<|im_start|>", "[/INST]", "Text to translate:", "Hindi Translation:", "नोट:", "Note:", "संक्षेप:", "Translation Notes:"]:
                translated_text = translated_text.split(sep)[0].strip()

            # Strip wrapping quotes
            if translated_text.startswith('"') and translated_text.endswith('"'):
                translated_text = translated_text[1:-1].strip()
            if translated_text.startswith("'") and translated_text.endswith("'"):
                translated_text = translated_text[1:-1].strip()

            # Apply cleaning to fix any minor transliteration or script leaks from llama
            translated_text = LanguageService.clean_translated_hindi(translated_text)

            # Validate — fall back to English if garbage
            if not LanguageService._is_valid_hindi_output(text, translated_text):
                return text

            return translated_text

        except Exception as e:
            print(f"   Hindi translation failed: {e}")
            return text

    @staticmethod
    def translate_to_hinglish(text: str) -> str:
        """Convert Devanagari Hindi text into a Roman-script Hinglish answer."""
        if not text or not text.strip():
            return text

        try:
            from app.services.admin_config_service import admin_config_service
            config = admin_config_service.get_config()
            if not config.get("translation_enabled", True):
                return text
        except Exception:
            config = {}

        # Prefer a local model conversion for natural Hinglish output.
        try:
            from langchain_community.llms import Ollama
            from app.core.config import settings

            print(f"   [Converting Hindi to Hinglish using local model {settings.TRANSLATION_MODEL}...]")
            local_translator = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.TRANSLATION_MODEL,
                temperature=0,
                num_ctx=4096,
                timeout=120
            )
            prompt = (
                "You are a translator that converts Hindi written in Devanagari script into natural, conversational Roman-script Hinglish.\n"
                "Preserve all formatting, bullets, numbered lists, headings, and line breaks exactly.\n"
                "Keep abbreviations and technical terms like EMD, GFR, GeM, L1, DSC, CRN, PAN, GST, and portal names unchanged.\n"
                "Do NOT output any Devanagari or other non-Latin script.\n"
                "Output only the Hinglish translation without any explanations.\n\n"
                f"Text:\n{text}\n\nHinglish:"
            )
            translated_text = local_translator.invoke(prompt).strip()
            for sep in ["Hinglish:", "Translation:", "Note:", "नोट:", "Output:"]:
                if sep in translated_text:
                    translated_text = translated_text.split(sep)[-1].strip()

            if translated_text.startswith('"') and translated_text.endswith('"'):
                translated_text = translated_text[1:-1].strip()
            if translated_text.startswith("'") and translated_text.endswith("'"):
                translated_text = translated_text[1:-1].strip()

            if translated_text and not HINDI_RANGE.search(translated_text):
                return re.sub(r'\s+', ' ', translated_text).strip()
        except Exception as e:
            print(f"   [Hinglish conversion failed: {e}]")

        # Fallback: transliterate Hindi text to Latin script using indic-transliteration.
        try:
            import builtins
            if not hasattr(builtins, 'unicode'):
                builtins.unicode = str

            from indic_transliteration import sanscript
            from indic_transliteration.sanscript import transliterate

            raw = transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
            normalized = raw.lower()

            # Remove stray Devanagari characters that may appear in the transliteration output.
            normalized = re.sub(r'[\u0900-\u097F]+', '', normalized)

            replacements = {
                'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṝ': 'r', 'ṛ': 'r', 'ḷ': 'l',
                'ṅ': 'ng', 'ñ': 'n', 'ṇ': 'n', 'ś': 'sh', 'ṣ': 'sh',
                'ṭ': 't', 'ḍ': 'd', 'ḥ': 'h', 'ṃ': 'm', 'ṁ': 'm',
                'ē': 'e', 'ō': 'o', 'ç': 'ch', 'ǒ': 'o', 'á': 'a', 'é': 'e',
                'í': 'i', 'ó': 'o', 'ú': 'u', 'ä': 'a', 'ë': 'e', 'ï': 'i',
            }
            for src, dst in replacements.items():
                normalized = normalized.replace(src, dst)

            # Common Hinglish lexical fixes
            normalized = re.sub(r'\bhaiṃ\b', 'hain', normalized)
            normalized = re.sub(r'\bhaiṁ\b', 'hain', normalized)
            normalized = re.sub(r'\bjaṃ\b', 'jam', normalized)
            normalized = re.sub(r'\bjā\b', 'ja', normalized)
            normalized = re.sub(r'\bsaṃbhavit\b', 'sambhavit', normalized)
            normalized = re.sub(r'\bāyā\b', 'aya', normalized)
            normalized = re.sub(r'\bā\b', 'a', normalized)
            normalized = re.sub(r'\bī\b', 'i', normalized)
            normalized = re.sub(r'\s+', ' ', normalized).strip()

            normalized = re.sub(r'[\u0900-\u097F]+', '', normalized)
            if normalized and not HINDI_RANGE.search(normalized):
                return normalized
        except Exception as e:
            print(f"   [Hinglish romanization fallback failed: {e}]")

        return text

    @staticmethod
    def _is_network_translation_error(err_str: str) -> bool:
        return any(
            err in err_str
            for err in [
                "getaddrinfo failed", "unreachable host", "10065", "11001", "10060",
                "10054", "10061", "timed out", "timeout", "connection", "429", "Too Many Requests",
            ]
        )

    @staticmethod
    def translate_ingestion_chunk_local_ollama(text: str) -> str:
        """Translate a single document chunk to English during ingestion (not chat queries)."""
        if not text or not text.strip() or not LanguageService.is_hindi(text):
            return text
        try:
            from langchain_community.llms import Ollama
            from app.core.config import settings
            local_translator = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.TRANSLATION_MODEL,
                temperature=0,
                num_ctx=4096,
                timeout=120,
            )
            prompt = (
                "You are a professional Hindi to English translator specializing in government procurement.\n"
                "Translate the following Hindi document text into clean, natural English.\n"
                "Preserve numbers, rule references, page markers, and formatting.\n"
                "Output ONLY the English translation without notes or explanations.\n\n"
                f"Text:\n{text}\n\nEnglish Translation:"
            )
            res = local_translator.invoke(prompt).strip()
            for sep in ["English Translation:", "Translation:", "Note:"]:
                if sep in res:
                    res = res.split(sep)[-1].strip()
            return res or text
        except Exception as e:
            print(f"      [Ingestion chunk Ollama translation failed: {e}]")
            return text

    @staticmethod
    def translate_chunks_to_english(chunks_text: List[str]) -> List[str]:
        """Translate a list of Hindi chunks to English using batched Google Translate requests"""
        translated_all = []
        ingestion_offline = False

        # Dynamically batch chunks so combined character count is under 4200 (Google Translate limit is 5000)
        batches = []
        current_batch = []
        current_len = 0
        for chunk in chunks_text:
            chunk_len = len(chunk)
            if current_batch and (current_len + chunk_len + 15 > 4200):
                batches.append(current_batch)
                current_batch = [chunk]
                current_len = chunk_len
            else:
                current_batch.append(chunk)
                current_len += chunk_len + 15
        if current_batch:
            batches.append(current_batch)

        for batch_idx, batch in enumerate(batches, start=1):
            if ingestion_offline:
                print(f"      [Ingestion offline mode] Translating batch {batch_idx}/{len(batches)} ({len(batch)} chunks) via Ollama...")
                translated_batch = LanguageService.translate_batch_local_ollama(batch)
                translated_all.extend(translated_batch)
                continue

            # Only translate chunks that actually contain Hindi
            has_hindi = any(LanguageService.is_hindi(t) for t in batch)
            if not has_hindi:
                translated_all.extend(batch)
                continue

            delimiter = "\n=== CHUNK ===\n"
            combined = delimiter.join(batch)
            translated_batch = None

            for attempt in range(3):
                try:
                    res = GoogleTranslator(source='auto', target='en').translate(combined)
                    if res:
                        parts = re.split(r'===?\s*CHUNK\s*===?', res, flags=re.IGNORECASE)
                        parts = [p.strip() for p in parts]
                        if len(parts) == len(batch):
                            translated_batch = parts
                            break
                        print(
                            f"      [Batch split mismatch: got {len(parts)} parts, expected {len(batch)}. "
                            f"Retry {attempt + 1}/3..."
                        )
                except Exception as e:
                    err_str = str(e)
                    if LanguageService._is_network_translation_error(err_str):
                        print(f"      [Google Translate network error (attempt {attempt + 1}/3): {e}]")
                        time.sleep(2 + attempt * 2)
                        if attempt == 2:
                            print("      [Switching ingestion to local Ollama translation fallback.]")
                            ingestion_offline = True
                            translated_batch = LanguageService.translate_batch_local_ollama(batch)
                            translated_all.extend(translated_batch)
                            break
                    else:
                        print(f"      [Batch translation failed: {e}. Falling back to individual chunks.]")
                        break

            if ingestion_offline:
                continue

            if translated_batch is None:
                translated_batch = []
                for t in batch:
                    if LanguageService.is_hindi(t):
                        translated_batch.append(LanguageService.translate_ingestion_chunk_local_ollama(t))
                    else:
                        translated_batch.append(t)

            translated_all.extend(translated_batch)
            time.sleep(1.5)

        return translated_all

    @staticmethod
    def translate_batch_local_ollama(batch: List[str]) -> List[str]:
        """Translate a batch of chunks to English using the local Ollama model"""
        hindi_batch = [t for t in batch if LanguageService.is_hindi(t)]
        if not hindi_batch:
            return batch

        try:
            from langchain_community.llms import Ollama
            from app.core.config import settings
            local_translator = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.TRANSLATION_MODEL,
                temperature=0,
                num_ctx=4096,
                timeout=120,
            )

            delimiter = "\n=== CHUNK ===\n"
            combined = delimiter.join(hindi_batch)

            prompt = (
                "You are a professional Hindi to English translator specializing in government procurement.\n"
                "Translate the following Hindi text chunk by chunk into clean, natural English.\n"
                "Keep the delimiter '=== CHUNK ===' exactly where it is to separate the translated chunks.\n\n"
                "Constraints:\n"
                "- Output ONLY the English translations separated by '=== CHUNK ==='. Do NOT add any notes, headers, or explanations.\n\n"
                f"Content to translate:\n{combined}\n\n"
                "English Translation:"
            )
            res = local_translator.invoke(prompt).strip()
            parts = re.split(r'===?\s*CHUNK\s*===?', res, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts]
            if len(parts) == len(hindi_batch):
                translated_map = dict(zip(hindi_batch, parts))
                return [translated_map.get(t, t) for t in batch]
            print(f"      [Ollama batch count mismatch: got {len(parts)}, expected {len(hindi_batch)}. Falling back to individual.]")
        except Exception as e:
            print(f"      [Local batch Ollama translation failed: {e}]")

        return [
            LanguageService.translate_ingestion_chunk_local_ollama(t) if LanguageService.is_hindi(t) else t
            for t in batch
        ]

language_service = LanguageService()