# scripts/debug_rag.py
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Set stdout/stderr encoding for Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from app.core.rag_engine import get_rag_engine
from app.core.language import language_service

def test():
    question = "शॉर्ट टेंडर नोटिस के नियम क्या हैं?"
    role = "government_officer"
    
    print("=" * 80)
    print(f"Testing question: {question}")
    print(f"Role: {role}")
    print("=" * 80)
    
    # 1. Detect language
    detected_lang = language_service.detect_language(question)
    print(f"[Language Service] Detected Language: {detected_lang}")
    
    # 2. Translate to English
    eng_query = language_service.translate_to_english(question)
    print(f"[Language Service] Translated query: {eng_query}")
    
    # 3. Retrieve chunks
    engine = get_rag_engine()
    chunks = engine.retrieve_chunks(eng_query, role, k=7, original_query=question)
    print(f"\n[RAG Engine] Retrieved {len(chunks)} chunks:")
    for i, c in enumerate(chunks):
        print(f"\n--- Chunk {i+1} (Score: {c.get('score', 0.0):.2f}) ---")
        print(f"Source: {c['source']}")
        print(f"Content Preview: {c['content'][:300]}...")
        
    # 4. Generate Prompt
    context_parts = []
    sources = []
    total_chars = 0
    for c in chunks:
        truncated_content = engine.clean_truncate(c["content"], 2500)
        context_parts.append(truncated_content)
        if c["source"] not in sources:
            sources.append(c["source"])
    context = "\n\n---\n\n".join(context_parts)
    
    is_gfr_query = any(w in eng_query.lower() for w in ["gfr", "rule", "gem", "emd", "bid security", "tender", "msme"])
    gfr_rule_mapping_instructions = """
Key GFR Rules (cite exactly): Rule 144=buying principles; Rule 149=GeM portal; Rule 154=purchase without quotation (up to ₹50k); Rule 155=Local Purchase Committee (₹50k–₹2.5L); Rule 161=Advertised/Open Tender (above ₹25L); Rule 162=Limited Tender (up to ₹25L, min 3 suppliers); Rule 163=Two-bid system; Rule 166=Single Tender (proprietary/emergency); Rule 170=EMD/Bid Security (2–5%, MSEs/Startups exempt); Rule 171=Performance Security (3–10%); Rules 177–196=Procurement of Services.
""" if is_gfr_query else ""
    
    formatting_instructions = """
**Response Format:**
- If answering about a **process or step-by-step procedure**: use numbered steps (1. 2. 3. ...) with clear action-oriented language. Group related steps logically with brief headers if helpful.
- If answering about **general policy or rules**: use bullet points organized by category/topic.
- For **page references**, place them at end of each statement in square brackets like [Page 5] when necessary.
- Keep each step/point brief (1-2 lines). Avoid long paragraphs.
- Use simple, clear language without jargon.
"""
    try:
        from app.services.admin_config_service import admin_config_service
        config = admin_config_service.get_config()
    except Exception:
        config = {}
    
    officer_prompt_tpl = config.get("officer_prompt", "")
    prompt = officer_prompt_tpl.format(
        formatting_instructions=formatting_instructions,
        gfr_rule_mapping_instructions=gfr_rule_mapping_instructions,
        context=context,
        english_query=eng_query
    )
    
    from app.core.config import settings
    is_mistral = "mistral" in settings.LLM_MODEL.lower()
    if is_mistral:
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
    else:
        formatted_prompt = prompt
        
    print("\n[RAG Engine] LLM Model: ", settings.LLM_MODEL)
    print("\n[RAG Engine] Querying LLM...")
    answer_raw = engine.llm.invoke(formatted_prompt).strip()
    print("\n[RAG Engine] Raw English LLM response:")
    print("-" * 50)
    print(answer_raw)
    print("-" * 50)
    
    # 5. Translate back to Hindi
    print("\n[Language Service] Translating to Hindi...")
    final_answer = language_service.translate_to_hindi(answer_raw)
    print("\n[Language Service] Hindi response:")
    print("-" * 50)
    with open("scripts/debug_rag_output.txt", "w", encoding="utf-8") as out_f:
        out_f.write(final_answer)
    print("Hindi response written to scripts/debug_rag_output.txt")
    print("-" * 50)

if __name__ == "__main__":
    test()
