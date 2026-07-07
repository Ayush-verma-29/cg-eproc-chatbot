import os
import sys
import re
import json
from pathlib import Path
import fitz  # PyMuPDF
import urllib.request
import urllib.error

# Set output encoding to UTF-8 for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.core.config import settings

OLLAMA_GENERATE_URL = f"{settings.OLLAMA_BASE_URL}/api/generate"
MODEL_NAME = settings.LLM_MODEL

def extract_snippet(file_path):
    """Extract a small text snippet from the first page of the file to identify its context."""
    ext = file_path.suffix.lower()
    text = ""
    try:
        if ext == '.pdf':
            doc = fitz.open(file_path)
            if len(doc) > 0:
                text = doc[0].get_text()[:600]
            doc.close()
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read(600)
        elif ext == '.docx':
            # Basic fallback for docx
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs[:5]])[:600]
            except Exception:
                text = ""
    except Exception as e:
        print(f"   Warning: Could not extract snippet from {file_path.name}: {e}")
    return text.strip()

def get_keywords_from_text(text, filename):
    """Extract a few keywords from the text or filename for context-aware fallback questions."""
    # Clean filename to use as keywords
    clean_name = re.sub(r'[\-_.]', ' ', filename).replace('pdf', '').replace('docx', '').replace('txt', '').strip()
    words = clean_name.split()
    
    # Simple list of core concepts
    core_concepts = []
    for w in words:
        if len(w) > 3 and w.lower() not in ['final', 'upto', 'rule', 'rules', 'manual', 'policy', 'guidelines', 'notice', 'precision']:
            core_concepts.append(w)
            
    if not core_concepts:
        core_concepts = words[:3] if words else ["Procurement"]
        
    return " ".join(core_concepts)

def query_ollama_for_questions(filename, snippet, keywords, is_govt):
    """Query local Ollama to generate 5 English and 5 Hindi questions based on snippet context."""
    role = "government procurement officer rules" if is_govt else "vendor portal usage"
    prompt = f"""You are a testing assistant. Generate exactly 10 test questions (5 in English, and 5 in Hindi) that a user would ask a chatbot about this document.
Document Name: {filename}
Role: {role}
Keywords: {keywords}
Content Snippet:
{snippet}

Format your response exactly as a JSON array of objects, where each object has:
- "question": the question string
- "language": either "en" or "hi"

Do not write any introduction, code block formatting, or explanation. Only output the raw JSON array containing exactly 10 items.
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            OLLAMA_GENERATE_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        # 12 second timeout
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            response_text = res_data.get('response', '').strip()
            
            # Find JSON array using regex in case LLM added conversational text
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group(0))
                if len(questions) >= 8: # Acceptable count
                    return questions
    except Exception as e:
        # Ignore and fall back
        pass
    return None

def generate_templated_questions(filename, keywords, is_govt):
    """Generate 10 context-aware fallback questions (5 English, 5 Hindi) when Ollama is offline."""
    subject = keywords if keywords else "this document"
    
    if is_govt:
        en_questions = [
            f"What are the main guidelines mentioned in {filename}?",
            f"What does {filename} regulate regarding {subject}?",
            f"Under GFR and government rules, what is the procedure for {subject}?",
            f"Where can I find the specific sections about {subject} in {filename}?",
            f"What is the core objective of {filename}?"
        ]
        hi_questions = [
            f"{filename} में {subject} के संबंध में मुख्य दिशा-निर्देश क्या हैं?",
            f"{filename} के तहत {subject} के लिए क्या प्रक्रिया निर्धारित है?",
            f"सरकारी नियमों के अनुसार {filename} का मुख्य उद्देश्य क्या है?",
            f"मुझे {filename} में {subject} से संबंधित नियम कहाँ मिल सकते हैं?",
            f"क्या {filename} के अनुसार {subject} के नियमों का पालन करना अनिवार्य है?"
        ]
    else:
        en_questions = [
            f"How do I use the system according to the {filename}?",
            f"What is the step-by-step process for {subject} in {filename}?",
            f"What system settings or configurations are needed for {subject} in {filename}?",
            f"Where can a vendor find details about {subject} in {filename}?",
            f"What are the troubleshooting steps mentioned in {filename}?"
        ]
        hi_questions = [
            f"{filename} के अनुसार {subject} की चरण-दर-चरण प्रक्रिया क्या है?",
            f"विक्रेताओं के लिए {filename} में {subject} से संबंधित क्या निर्देश हैं?",
            f"{filename} के अनुसार {subject} के लिए आवश्यक सिस्टम सेटिंग्स क्या हैं?",
            f"यदि {filename} के अनुसार {subject} में कोई समस्या आए तो क्या करें?",
            f"{filename} के तहत {subject} के मुख्य बिंदु क्या हैं?"
        ]
        
    combined = []
    for q in en_questions:
        combined.append({"question": q, "language": "en"})
    for q in hi_questions:
        combined.append({"question": q, "language": "hi"})
        
    return combined

def main():
    print("=" * 70)
    print("  CG e-Procurement Chatbot - Test Question Generator")
    print("=" * 70)
    
    govt_dir = Path(settings.GOVT_PDF_DIR)
    vendor_dir = Path(settings.VENDOR_PDF_DIR)
    
    all_questions = []
    
    # Process Govt Files
    print(f"\n📂 Processing Govt Rules directory: {govt_dir}")
    govt_files = sorted(list(govt_dir.glob('*')))
    govt_files = [f for f in govt_files if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']]
    
    print(f"📄 Found {len(govt_files)} files in govt_rules")
    for i, file_path in enumerate(govt_files):
        print(f"   [{i+1}/{len(govt_files)}] File: {file_path.name}")
        snippet = extract_snippet(file_path)
        keywords = get_keywords_from_text(snippet, file_path.name)
        
        # Try Ollama, fallback to templates
        q_list = query_ollama_for_questions(file_path.name, snippet, keywords, is_govt=True)
        if q_list:
            print("      -> Generated via Ollama LLM")
        else:
            q_list = generate_templated_questions(file_path.name, keywords, is_govt=True)
            print("      -> Generated via Context Templates (Ollama offline/busy)")
            
        for q in q_list:
            q["source_file"] = file_path.name
            q["category"] = "government_rules"
            all_questions.append(q)
            
    # Process Vendor Files
    print(f"\n📂 Processing Vendor Manuals directory: {vendor_dir}")
    vendor_files = sorted(list(vendor_dir.glob('*')))
    vendor_files = [f for f in vendor_files if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']]
    
    print(f"📄 Found {len(vendor_files)} files in vendor_manuals")
    for i, file_path in enumerate(vendor_files):
        print(f"   [{i+1}/{len(vendor_files)}] File: {file_path.name}")
        snippet = extract_snippet(file_path)
        keywords = get_keywords_from_text(snippet, file_path.name)
        
        # Try Ollama, fallback to templates
        q_list = query_ollama_for_questions(file_path.name, snippet, keywords, is_govt=False)
        if q_list:
            print("      -> Generated via Ollama LLM")
        else:
            q_list = generate_templated_questions(file_path.name, keywords, is_govt=False)
            print("      -> Generated via Context Templates (Ollama offline/busy)")
            
        for q in q_list:
            q["source_file"] = file_path.name
            q["category"] = "vendor_manuals"
            all_questions.append(q)
            
    # Save results
    output_path = Path(__file__).parent.parent / "scripts" / "test_questions.json"
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(all_questions, out_f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 70)
    print("🎉 QUESTION GENERATION COMPLETED!")
    print(f"   Total questions generated: {len(all_questions)}")
    print(f"   Output saved to: {output_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
