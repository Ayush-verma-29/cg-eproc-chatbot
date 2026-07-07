# backend/app/core/procurement_dict.py
"""
Domain-specific dictionary for procurement terminology
This dictionary should ONLY GROW - never remove terms, only add new ones
"""

import re

# ============================================================
# CORE PROCUREMENT DICTIONARY - ADD NEW TERMS HERE ONLY
# ============================================================

PROCUREMENT_DICTIONARY = {
    # ============ Core Procurement Terms ============
    "EMD": {
        "hi": ["ईएमडी", "सुरक्षा निधि", "ईमानदारी जमा", "जमानत राशि", "अमानत राशि"],
        "en": "Earnest Money Deposit"
    },
    "Bid Security": {
        "hi": ["बोली सुरक्षा", "निविदा सुरक्षा", "ईएमडी", "बोली जमानत"],
        "en": "Bid Security"
    },
    "Performance Security": {
        "hi": ["प्रदर्शन सुरक्षा", "कार्य निष्पादन गारंटी", "प्रदर्शन गारंटी"],
        "en": "Performance Security"
    },
    "Tender": {
        "hi": ["निविदा", "टेंडर", "बोली", "ठेका", "काम"],
        "en": "Tender"
    },
    "Bid": {
        "hi": ["बोली", "निविदा", "प्रस्ताव", "दर"],
        "en": "Bid"
    },
    "Contract": {
        "hi": ["अनुबंध", "करार", "संविदा", "ठेका", "समझौता"],
        "en": "Contract"
    },
    "Procurement": {
        "hi": ["क्रय", "खरीद", "प्राप्ति", "खरीदारी", "अधिग्रहण"],
        "en": "Procurement"
    },
    "Purchase": {
        "hi": ["क्रय", "खरीद", "खरीदारी"],
        "en": "Purchase"
    },
    
    # ============ GFR Rules ============
    "GFR": {
        "hi": ["जीएफआर", "सामान्य वित्तीय नियम", "वित्तीय नियम", "जनरल फाइनेंशियल रूल्स"],
        "en": "General Financial Rules"
    },
    "Rule": {
        "hi": ["नियम", "नियम संख्या", "नियमावली", "नियम क्रमांक", "नियम"],
        "en": "Rule"
    },
    "Section": {
        "hi": ["धारा", "अनुभाग", "खंड", "सेक्शन"],
        "en": "Section"
    },
    "Clause": {
        "hi": ["उपबंध", "खंड", "शर्त", "क्लॉज"],
        "en": "Clause"
    },
    "Chapter": {
        "hi": ["अध्याय", "प्रकरण", "चैप्टर"],
        "en": "Chapter"
    },
    "Sub-rule": {
        "hi": ["उपनियम", "उप-नियम"],
        "en": "Sub-rule"
    },
    
    # ============ CVC / Vigilance ============
    "CVC": {
        "hi": ["सीवीसी", "केंद्रीय सतर्कता आयोग", "सतर्कता आयोग", "सेंट्रल विजिलेंस कमीशन"],
        "en": "Central Vigilance Commission"
    },
    "Vigilance": {
        "hi": ["सतर्कता", "निगरानी", "विजिलेंस"],
        "en": "Vigilance"
    },
    "Integrity": {
        "hi": ["ईमानदारी", "सत्यनिष्ठा", "अखंडता"],
        "en": "Integrity"
    },
    "Corruption": {
        "hi": ["भ्रष्टाचार", "अनाचार", "भ्रष्टाचार"],
        "en": "Corruption"
    },
    "Debarment": {
        "hi": ["प्रतिबंध", "बहिष्कार", "काली सूची", "प्रतिबंधन"],
        "en": "Debarment"
    },
    "Blacklist": {
        "hi": ["काली सूची", "प्रतिबंधित सूची", "ब्लैकलिस्ट"],
        "en": "Blacklist"
    },
    
    # ============ GeM Portal ============
    "GeM": {
        "hi": ["जीईएम", "जेम", "सरकारी ई-बाजार", "गवर्नमेंट ई-मार्केटप्लेस"],
        "en": "Government e-Marketplace"
    },
    "CPPP": {
        "hi": ["सीपीपीपी", "केंद्रीय सार्वजनिक खरीद पोर्टल", "सेंट्रल पब्लिक प्रोक्योरमेंट पोर्टल"],
        "en": "Central Public Procurement Portal"
    },
    "e-Procurement": {
        "hi": ["ई-प्रोक्योरमेंट", "ई-निविदा", "ऑनलाइन निविदा", "ई-प्रोक्योरमेंट"],
        "en": "Electronic Procurement"
    },
    "Reverse Auction": {
        "hi": ["रिवर्स नीलामी", "उल्टी नीलामी", "ई-रिवर्स नीलामी"],
        "en": "Reverse Auction"
    },
    
    # ============ Tender Types ============
    "OTE": {
        "hi": ["ओटीई", "खुली निविदा", "खुली बोली", "ओपन टेंडर"],
        "en": "Open Tender Enquiry"
    },
    "LTE": {
        "hi": ["एलटीई", "सीमित निविदा", "लिमिटेड टेंडर"],
        "en": "Limited Tender Enquiry"
    },
    "STE": {
        "hi": ["एसटीई", "एकल निविदा", "सिंगल टेंडर"],
        "en": "Single Tender Enquiry"
    },
    "PAC": {
        "hi": ["पीएसी", "प्रोपराइटरी प्रमाण पत्र", "प्रोपराइटरी आर्टिकल सर्टिफिकेट"],
        "en": "Proprietary Article Certificate"
    },
    "Global Tender": {
        "hi": ["ग्लोबल टेंडर", "अंतर्राष्ट्रीय निविदा", "जीटीई"],
        "en": "Global Tender Enquiry"
    },
    
    # ============ Bid Process ============
    "Technical Bid": {
        "hi": ["तकनीकी बोली", "तकनीकी निविदा", "टेक्निकल बिड"],
        "en": "Technical Bid"
    },
    "Financial Bid": {
        "hi": ["वित्तीय बोली", "मूल्य बोली", "आर्थिक प्रस्ताव", "फाइनेंशियल बिड"],
        "en": "Financial Bid"
    },
    "BOQ": {
        "hi": ["बीओक्यू", "मात्रा सूची", "बिल ऑफ क्वांटिटी", "बिल ऑफ मटेरियल"],
        "en": "Bill of Quantities"
    },
    "RFP": {
        "hi": ["आरएफपी", "प्रस्ताव आमंत्रण", "रिक्वेस्ट फॉर प्रपोजल"],
        "en": "Request for Proposal"
    },
    "RFQ": {
        "hi": ["आरएफक्यू", "उद्धरण आमंत्रण", "रिक्वेस्ट फॉर कोटेशन"],
        "en": "Request for Quotation"
    },
    "EOI": {
        "hi": ["ईओआई", "अभिरुचि पत्र", "इच्छा व्यक्ति पत्र", "एक्सप्रेशन ऑफ इंटरेस्ट"],
        "en": "Expression of Interest"
    },
    "NIT": {
        "hi": ["एनआईटी", "निविदा सूचना", "नोटिस इनवाइटिंग टेंडर"],
        "en": "Notice Inviting Tender"
    },
    
    # ============ Security & Payments ============
    "BG": {
        "hi": ["बीजी", "बैंक गारंटी", "बैंक गारंटी"],
        "en": "Bank Guarantee"
    },
    "Bank Guarantee": {
        "hi": ["बैंक गारंटी", "बीजी"],
        "en": "Bank Guarantee"
    },
    "DD": {
        "hi": ["डीडी", "डिमांड ड्राफ्ट", "डिमांड ड्राफ्ट"],
        "en": "Demand Draft"
    },
    "FDR": {
        "hi": ["एफडीआर", "सावधि जमा प्रमाण पत्र", "फिक्स्ड डिपॉजिट रसीद"],
        "en": "Fixed Deposit Receipt"
    },
    "Refund": {
        "hi": ["वापसी", "रिफंड", "लौटाई", "वापस"],
        "en": "Refund"
    },
    "Payment": {
        "hi": ["भुगतान", "भुगतान", "भुगतान करना"],
        "en": "Payment"
    },
    "Advance Payment": {
        "hi": ["अग्रिम भुगतान", "एडवांस पेमेंट"],
        "en": "Advance Payment"
    },
    
    # ============ Documents ============
    "DSC": {
        "hi": ["डीएससी", "डिजिटल हस्ताक्षर प्रमाण पत्र", "डिजिटल सर्टिफिकेट"],
        "en": "Digital Signature Certificate"
    },
    "Digital Signature": {
        "hi": ["डिजिटल हस्ताक्षर", "डिजिटल सिग्नेचर"],
        "en": "Digital Signature"
    },
    "PAN": {
        "hi": ["पैन", "स्थायी खाता संख्या", "पैन कार्ड"],
        "en": "Permanent Account Number"
    },
    "GST": {
        "hi": ["जीएसटी", "वस्तु एवं सेवा कर", "जीएसटी"],
        "en": "Goods and Services Tax"
    },
    "TIN": {
        "hi": ["टीआईएन", "कर पहचान संख्या", "टीआईएन"],
        "en": "Tax Identification Number"
    },
    
    # ============ Vendor Related ============
    "Vendor": {
        "hi": ["वेंडर", "विक्रेता", "आपूर्तिकर्ता", "विक्रेता", "ठेकेदार"],
        "en": "Vendor"
    },
    "Supplier": {
        "hi": ["आपूर्तिकर्ता", "विक्रेता", "सप्लायर"],
        "en": "Supplier"
    },
    "Bidder": {
        "hi": ["बोलीदाता", "निविदाकर्ता", "बिडर"],
        "en": "Bidder"
    },
    "Contractor": {
        "hi": ["ठेकेदार", "अनुबंधकर्ता", "कांट्रेक्टर"],
        "en": "Contractor"
    },
    "Registration": {
        "hi": ["पंजीकरण", "रजिस्ट्रेशन", "रजिस्टर"],
        "en": "Registration"
    },
    
    # ============ MSE/MSME ============
    "MSE": {
        "hi": ["एमएसई", "लघु उद्योग", "सूक्ष्म उद्योग", "छोटे उद्योग"],
        "en": "Micro and Small Enterprise"
    },
    "MSME": {
        "hi": ["एमएसएमई", "सूक्ष्म लघु एवं मध्यम उद्योग", "माइक्रो स्मॉल मीडियम एंटरप्राइज"],
        "en": "Micro, Small and Medium Enterprises"
    },
    "NSIC": {
        "hi": ["एनएसआईसी", "राष्ट्रीय लघु उद्योग निगम"],
        "en": "National Small Industries Corporation"
    },
    
    # ============ Time & Validity ============
    "Bid Validity": {
        "hi": ["बोली वैधता", "निविदा वैधता अवधि", "बिड वैलिडिटी"],
        "en": "Bid Validity Period"
    },
    "Extension": {
        "hi": ["विस्तार", "बढ़ाना", "समय वृद्धि", "एक्सटेंशन"],
        "en": "Extension"
    },
    "Deadline": {
        "hi": ["अंतिम तिथि", "समय सीमा", "नियत तारीख", "डेडलाइन"],
        "en": "Deadline"
    },
    "Force Majeure": {
        "hi": ["अप्रत्याशित घटना", "आपात स्थिति", "फोर्स मेजर"],
        "en": "Force Majeure"
    },
    "Liquidated Damages": {
        "hi": ["हर्जाना", "निर्धारित क्षतिपूर्ति", "लिक्विडेटेड डैमेजेस"],
        "en": "Liquidated Damages"
    },
    
    # ============ Amendments & Changes ============
    "Amendment": {
        "hi": ["संशोधन", "संशोधित", "बदलाव", "एमेंडमेंट"],
        "en": "Amendment"
    },
    "Corrigendum": {
        "hi": ["परिशोधन", "सुधार पत्र", "संशोधन", "कोरिजेंडम"],
        "en": "Corrigendum"
    },
    "Variation": {
        "hi": ["भिन्नता", "बदलाव", "अंतर", "वेरिएशन"],
        "en": "Variation"
    },
    "Deviation": {
        "hi": ["विचलन", "अपवाद", "डिविएशन"],
        "en": "Deviation"
    },
    
    # ============ Evaluation & Award ============
    "L1": {
        "hi": ["एल-1", "न्यूनतम बोलीदाता", "सबसे कम बोली", "लोवेस्ट बिडर"],
        "en": "Lowest Bidder"
    },
    "Evaluation": {
        "hi": ["मूल्यांकन", "मूल्यांकन करना", "इवैल्यूएशन"],
        "en": "Evaluation"
    },
    "Award": {
        "hi": ["पुरस्कार", "आवंटन", "प्रदान", "अवार्ड"],
        "en": "Award"
    },
    
    # ============ Conflict of Interest ============
    "COI": {
        "hi": ["सीओआई", "हितों का टकराव", "कॉन्फ्लिक्ट ऑफ इंटरेस्ट"],
        "en": "Conflict of Interest"
    },
    "Conflict of Interest": {
        "hi": ["हितों का टकराव", "हित संघर्ष", "कॉन्फ्लिक्ट ऑफ इंटरेस्ट"],
        "en": "Conflict of Interest"
    },
    
    # ============ Quality & Inspection ============
    "Inspection": {
        "hi": ["निरीक्षण", "जाँच", "इंस्पेक्शन", "परीक्षण"],
        "en": "Inspection"
    },
    "Quality Assurance": {
        "hi": ["गुणवत्ता आश्वासन", "गुणवत्ता सुनिश्चितता", "क्वालिटी एश्योरेंस"],
        "en": "Quality Assurance"
    },
    "ISO": {
        "hi": ["आईएसओ", "अंतर्राष्ट्रीय मानक संगठन"],
        "en": "International Organization for Standardization"
    },
    
    # ============ Browsers & Technology ============
    "Internet Explorer": {
        "hi": ["इंटरनेट एक्सप्लोरर", "आईई", "इंटरनेट एक्सप्लोरर ब्राउज़र", "इंटरनेट एक्सप्लोरर"],
        "en": "Internet Explorer"
    },
    "Chrome": {
        "hi": ["क्रोम", "गूगल क्रोम", "क्रोम ब्राउज़र", "गूगल क्रोम"],
        "en": "Chrome"
    },
    "Edge": {
        "hi": ["एज", "माइक्रोसॉफ्ट एज", "एज ब्राउज़र", "माइक्रोसॉफ्ट एज"],
        "en": "Edge"
    },
    "Firefox": {
        "hi": ["फायरफॉक्स", "मोज़िला फायरफॉक्स", "फायरफॉक्स"],
        "en": "Firefox"
    },
    "IE Tab": {
        "hi": ["आईई टैब", "क्रोम के लिए आईई टैब", "आईई टैब"],
        "en": "IE Tab"
    },
    "Java": {
        "hi": ["जावा", "जावा रनटाइम", "जावा", "जावा"],
        "en": "Java Runtime Environment"
    },
    
    # ============ General Terms ============
    "Approval": {
        "hi": ["अनुमोदन", "स्वीकृति", "अप्रूवल"],
        "en": "Approval"
    },
    "Sanction": {
        "hi": ["अनुमति", "आज्ञा", "स्वीकृति", "सेंक्शन"],
        "en": "Sanction"
    },
    "Authority": {
        "hi": ["प्राधिकारी", "अधिकारी", "सक्षम प्राधिकारी", "अथॉरिटी"],
        "en": "Authority"
    },
    "Competent Authority": {
        "hi": ["सक्षम प्राधिकारी", "अधिकृत प्राधिकारी", "कम्पीटेंट अथॉरिटी"],
        "en": "Competent Authority"
    },
    
    # ============ Verbs & Actions ============
    "upload": {
        "hi": ["अपलोड", "अपलोड करें", "अपलोड करना"],
        "en": "upload"
    },
    "download": {
        "hi": ["डाउनलोड", "डाउनलोड करें", "डाउनलोड करना"],
        "en": "download"
    },
    "submit": {
        "hi": ["जमा", "सबमिट", "प्रस्तुत", "जमा करें"],
        "en": "submit"
    },
    "verify": {
        "hi": ["सत्यापित", "जांचें", "पुष्टि", "वेरिफाई"],
        "en": "verify"
    },
    "approve": {
        "hi": ["अनुमोदित", "स्वीकार", "अप्रूव"],
        "en": "approve"
    },
    "reject": {
        "hi": ["अस्वीकार", "निरस्त", "रद्द", "रिजेक्ट"],
        "en": "reject"
    },
    
    # ============ Hindi to English Direct Mapping ============
    # Additional Hindi terms that map directly to English
    "टेंडर": {"hi": ["टेंडर"], "en": "Tender"},
    "बोली": {"hi": ["बोली"], "en": "Bid"},
    "दर": {"hi": ["दर"], "en": "Rate"},
    "मूल्य": {"hi": ["मूल्य"], "en": "Price"},
    "समय": {"hi": ["समय"], "en": "Time"},
    "तिथि": {"hi": ["तिथि"], "en": "Date"},
    "विभाग": {"hi": ["विभाग"], "en": "Department"},
    "सरकार": {"hi": ["सरकार"], "en": "Government"},
    "नियमावली": {"hi": ["नियमावली"], "en": "Manual"},
    "दस्तावेज": {"hi": ["दस्तावेज"], "en": "Document"},
    "प्रपत्र": {"hi": ["प्रपत्र"], "en": "Form"},
    "हस्ताक्षर": {"hi": ["हस्ताक्षर"], "en": "Signature"},
    "प्रमाण पत्र": {"hi": ["प्रमाण पत्र"], "en": "Certificate"},
    "आवेदन": {"hi": ["आवेदन"], "en": "Application"},
    "सूचना": {"hi": ["सूचना"], "en": "Notice"},
    "अधिसूचना": {"hi": ["अधिसूचना"], "en": "Notification"},
    "आदेश": {"hi": ["आदेश"], "en": "Order"},
    "निर्णय": {"hi": ["निर्णय"], "en": "Decision"},
    "अपील": {"hi": ["अपील"], "en": "Appeal"},
    "शिकायत": {"hi": ["शिकायत"], "en": "Complaint"},
    "अनुशंसा": {"hi": ["अनुशंसा"], "en": "Recommendation"},
    "कार्यान्वयन": {"hi": ["कार्यान्वयन"], "en": "Implementation"},
    "निगरानी": {"hi": ["निगरानी"], "en": "Monitoring"},
    "समीक्षा": {"hi": ["समीक्षा"], "en": "Review"},
    "रिपोर्ट": {"hi": ["रिपोर्ट"], "en": "Report"},
    "लाभ": {"hi": ["लाभ"], "en": "Benefit"},
    "छूट": {"hi": ["छूट"], "en": "Exemption"},
}

# ============================================================
# MAPPINGS DERIVED FROM DICTIONARY - DO NOT EDIT DIRECTLY
# These are auto-generated from PROCUREMENT_DICTIONARY
# ============================================================

# Build reverse mapping (Hindi -> English)
HINDI_TO_ENGLISH = {}
for en_term, data in PROCUREMENT_DICTIONARY.items():
    for hi_term in data["hi"]:
        HINDI_TO_ENGLISH[hi_term.lower()] = en_term

# Build English to Hindi mapping (for response translation)
ENGLISH_TO_HINDI = {}
for en_term, data in PROCUREMENT_DICTIONARY.items():
    ENGLISH_TO_HINDI[en_term.lower()] = data["hi"][0]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def translate_query(text: str) -> str:
    """Translate Hindi query to English for better search"""
    result = text
    # Sort by length (longest first) to avoid partial replacements
    sorted_terms = sorted(HINDI_TO_ENGLISH.keys(), key=len, reverse=True)
    
    for hi_term in sorted_terms:
        if hi_term in result.lower():
            en_term = HINDI_TO_ENGLISH[hi_term]
            # Case-insensitive replacement
            pattern = re.compile(re.escape(hi_term), re.IGNORECASE)
            result = pattern.sub(en_term, result)
    
    return result

def get_hindi_translation(english_term: str) -> str:
    """Get Hindi translation for an English term"""
    term_lower = english_term.lower()
    if term_lower in ENGLISH_TO_HINDI:
        return ENGLISH_TO_HINDI[term_lower]
    return english_term

def get_all_terms() -> list:
    """Get all dictionary terms for debugging"""
    return list(PROCUREMENT_DICTIONARY.keys())