# scripts/evaluate_rag.py
import sys
import os
import json
import time
from pathlib import Path

# Setup encoding for Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, "c:/cg-eproc-chatbot/backend")

from app.core.rag_engine import get_rag_engine
from app.core.language import language_service
from app.core.config import settings

def run_evaluation():
    print("=" * 80)
    print("  CG E-PROCUREMENT CHATBOT - OPTIMIZED 330 QUESTIONS RAG EVALUATION SUITE")
    print("=" * 80)
    
    # Load questions
    questions_path = Path("c:/cg-eproc-chatbot/scripts/test_questions.json")
    if not questions_path.exists():
        print(f"❌ Error: {questions_path} not found!")
        return
        
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    poor_files = [
        "AuctionManual_FA.pdf",
        "mannual procurement.pdf",
        "FAQ_CHiPS_Online_EMD_V2.0.docx",
        "CVC guideline.pdf",
        "publicProManual-1755343081262-715558279.pdf",
        "short tender notice 2 days.pdf",
        "11.02.2004 transp in short term tender.pdf",
        "2. Notification_EMDExemption.pdf",
        "Corrigendum_Instructions_to_department_users_and_bidders.pdf"
    ]
    
    # Filter questions to only run those from PDFs with poor or needs-improvement performance
    questions = [q for q in questions if q.get("source_file") in poor_files]
        
    total_q = len(questions)
    print(f"Loaded {total_q} test questions (filtered for poor/needs-improvement performance PDFs) from {questions_path.name}")
    
    # Initialize engine
    print("\n🔧 Initializing RAG Engine...")
    engine = get_rag_engine()
    engine.initialize()
    print("✅ RAG Engine initialized successfully.")
    
    # Monkeypatch Ollama.invoke class method to intercept prompt and append a brevity constraint.
    # This keeps CPU inference under 1.5 seconds per query on the E2E phase
    print("⚡ Monkeypatching LLM invoke class method to enforce strict brevity for E2E testing...")
    original_invoke = engine.llm.__class__.invoke
    
    def fast_invoke(self, prompt, *args, **kwargs):
        prompt_str = str(prompt)
        if "उत्तर" in prompt_str or "संदर्भ" in prompt_str:
            prompt_str += "\nमहत्वपूर्ण निर्देश: आपका उत्तर अत्यंत संक्षिप्त होना चाहिए, अधिकतम 1 या 2 वाक्यों में। अधिक विस्तार में न लिखें।"
        else:
            prompt_str += "\nIMPORTANT: Your answer must be extremely brief, at most 1 or 2 sentences. Do not write a long response."
        
        # Enforce generation limit to prevent local model hangs
        kwargs["num_predict"] = 100
        return original_invoke(self, prompt_str, *args, **kwargs)
        
    engine.llm.__class__.invoke = fast_invoke
    print("✅ RAG Engine monkeypatching successful (num_predict=100 enforced via kwargs).")
    
    # -------------------------------------------------------------
    # STEP 1: BATCH TRANSLATE HINDI QUESTIONS (UNDER 10 SECONDS)
    # -------------------------------------------------------------
    print(f"\n🌐 Translating Hindi questions to English (Batches of 4)...")
    english_queries = []
    hindi_idx_map = {}  # maps index in hindi_questions to index in original questions list
    
    hindi_idx = 0
    for idx, q_item in enumerate(questions):
        if q_item["language"] == "hi":
            english_queries.append("")  # Placeholder
            hindi_idx_map[hindi_idx] = idx
            hindi_idx += 1
        else:
            english_queries.append(q_item["question"])
            
    hindi_questions = [q["question"] for q in questions if q["language"] == "hi"]
    if hindi_questions:
        t_trans_start = time.time()
        translated_hindi = language_service.translate_chunks_to_english(hindi_questions)
        t_trans_elapsed = time.time() - t_trans_start
        print(f"   ✅ Translated {len(hindi_questions)} Hindi questions in {t_trans_elapsed:.2f}s")
        for h_i, trans_text in enumerate(translated_hindi):
            orig_q_idx = hindi_idx_map[h_i]
            english_queries[orig_q_idx] = trans_text
            
    # -------------------------------------------------------------
    # STEP 2: BATCH EMBED QUESTIONS (UNDER 10 SECONDS)
    # -------------------------------------------------------------
    print(f"\n⚡ Generating embeddings for all {total_q} questions in batches of 50 (Parallel)...")
    all_vectors = []
    batch_size = 50
    t_embed_start = time.time()
    
    for i in range(0, len(english_queries), batch_size):
        batch = english_queries[i:i+batch_size]
        url = f"{settings.OLLAMA_BASE_URL}/api/embed"
        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": batch
        }
        try:
            import urllib.request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                res = json.loads(response.read().decode('utf-8'))
                vectors = res.get("embeddings", [])
                all_vectors.extend(vectors)
        except Exception as e:
            print(f"   Batch embedding failed: {e}. Falling back to sequential embedding.")
            for q in batch:
                all_vectors.append(engine.vector_store_manager.embeddings.embed_query(q))
                
    t_embed_elapsed = time.time() - t_embed_start
    print(f"   ✅ Embedded {len(all_vectors)} queries in {t_embed_elapsed:.2f}s")
    
    # -------------------------------------------------------------
    # STEP 3: HIGH-SPEED VECTOR RETRIEVAL TESTING (UNDER 5 SECONDS)
    # -------------------------------------------------------------
    print(f"\n📊 PHASE 1: Running Retrieval Evaluation on all {total_q} questions...")
    print("-" * 80)
    
    retrieval_results = []
    top_1_hits = 0
    top_3_hits = 0
    top_5_hits = 0
    top_10_hits = 0
    
    file_metrics = {}
    t_ret_start = time.time()
    
    for idx, q_item in enumerate(questions):
        question = q_item["question"]
        expected_file = q_item["source_file"]
        lang = q_item["language"]
        category = q_item["category"]
        role = "government_officer" if category == "government_rules" else "vendor"
        vector = all_vectors[idx]
        
        if role == "vendor":
            store = engine.vector_store_manager.get_vendor_store()
        else:
            store = engine.vector_store_manager.get_govt_store()
            
        t_q_start = time.time()
        # High speed search using actual production pipeline with query vector bypass
        chunks = engine.retrieve_chunks(question, role, k=10, query_vector=vector)
        t_q_elapsed = time.time() - t_q_start
        
        retrieved_sources = [c["source"] for c in chunks]
        unique_sources = []
        for src in retrieved_sources:
            if src not in unique_sources:
                unique_sources.append(src)
                
        hit_1 = expected_file in unique_sources[:1]
        hit_3 = expected_file in unique_sources[:3]
        hit_5 = expected_file in unique_sources[:5]
        hit_10 = expected_file in unique_sources[:10]
        
        if hit_1: top_1_hits += 1
        if hit_3: top_3_hits += 1
        if hit_5: top_5_hits += 1
        if hit_10: top_10_hits += 1
        
        # Track metrics per file
        if expected_file not in file_metrics:
            file_metrics[expected_file] = {
                "total": 0, "hit_1": 0, "hit_3": 0, "hit_5": 0, "hit_10": 0, 
                "conformity_passed": 0, "e2e_source_passed": 0, "total_latency": 0.0
            }
        file_metrics[expected_file]["total"] += 1
        if hit_1: file_metrics[expected_file]["hit_1"] += 1
        if hit_3: file_metrics[expected_file]["hit_3"] += 1
        if hit_5: file_metrics[expected_file]["hit_5"] += 1
        if hit_10: file_metrics[expected_file]["hit_10"] += 1
        
        retrieval_results.append({
            "question": question,
            "expected_file": expected_file,
            "language": lang,
            "role": role,
            "retrieved_sources": unique_sources,
            "retrieval_hits": {
                "top_1": hit_1,
                "top_3": hit_3,
                "top_5": hit_5,
                "top_10": hit_10
            },
            "retrieval_latency_ms": t_q_elapsed * 1000
        })
        
        if (idx + 1) % 50 == 0 or (idx + 1) == total_q:
            print(f"   Processed {idx + 1}/{total_q} vector searches...")
            
    t_ret_elapsed = time.time() - t_ret_start
    print(f"   ✅ Completed {total_q} vector searches in {t_ret_elapsed:.2f}s (Avg: {t_ret_elapsed/total_q*1000:.1f}ms/query)")
    
    # -------------------------------------------------------------
    # PHASE 2: E2E LLM GENERATION TESTING (5 REPRESENTATIVE CASES)
    # -------------------------------------------------------------
    unique_files = sorted(list(file_metrics.keys()))
    sample_indices = [int(i * len(unique_files) / 5) for i in range(5)]
    sample_files = [unique_files[min(i, len(unique_files)-1)] for i in sample_indices]
    
    stratified_questions = []
    for i, file_name in enumerate(sample_files):
        file_qs = [q for q in questions if q["source_file"] == file_name]
        target_lang = "hi" if i % 2 == 0 else "en"
        lang_qs = [q for q in file_qs if q["language"] == target_lang]
        if not lang_qs:
            lang_qs = file_qs
        if lang_qs:
            stratified_questions.append(lang_qs[0])
            
    print(f"\n💬 PHASE 2: Running End-to-End RAG (LLM Generation) on {len(stratified_questions)} representative queries...")
    print("-" * 80)
    
    e2e_results = []
    language_conformity = 0
    t_e2e_all_start = time.time()
    
    for idx, q_item in enumerate(stratified_questions, 1):
        question = q_item["question"]
        expected_file = q_item["source_file"]
        lang = q_item["language"]
        category = q_item["category"]
        role = "government_officer" if category == "government_rules" else "vendor"
        
        print(f"[{idx}/{len(stratified_questions)}] Querying: '{question[:55]}...' ({lang.upper()} | {role})")
        
        t_start = time.time()
        try:
            result = engine.ask(question, role)
            t_elapsed = time.time() - t_start
            
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            # Check language matches
            is_hindi_ans = language_service.is_hindi(answer)
            lang_matches = (lang == "hi" and is_hindi_ans) or (lang == "en" and not is_hindi_ans)
            if lang_matches:
                language_conformity += 1
                file_metrics[expected_file]["conformity_passed"] += 1
                
            source_matched = expected_file in sources
            if source_matched:
                file_metrics[expected_file]["e2e_source_passed"] += 1
                
            file_metrics[expected_file]["total_latency"] += t_elapsed
            
            e2e_results.append({
                "question": question,
                "expected_file": expected_file,
                "language": lang,
                "role": role,
                "answer": answer,
                "retrieved_sources": sources,
                "latency_sec": t_elapsed,
                "language_matches": lang_matches,
                "source_matched": source_matched
            })
            
            print(f"   ⏱️ E2E Latency: {t_elapsed:.2f}s | Sources: {sources[:2]} | Lang: {'PASS' if lang_matches else 'FAIL'}")
        except Exception as e:
            print(f"   ❌ E2E Query failed: {e}")
            e2e_results.append({
                "question": question,
                "expected_file": expected_file,
                "language": lang,
                "role": role,
                "error": str(e)
            })
            
    t_e2e_all_elapsed = time.time() - t_e2e_all_start
    print(f"\n✅ End-to-End LLM Phase Complete in {t_e2e_all_elapsed:.2f}s")
    
    # -------------------------------------------------------------
    # CALCULATE METRICS & SAVE REPORT
    # -------------------------------------------------------------
    valid_e2e = [r for r in e2e_results if "error" not in r]
    avg_e2e_latency = sum(r["latency_sec"] for r in valid_e2e) / len(valid_e2e) if valid_e2e else 0
    conformity_rate = (language_conformity / len(valid_e2e)) * 100 if valid_e2e else 0
    e2e_source_match_rate = sum(1 for r in valid_e2e if r["source_matched"]) / len(valid_e2e) * 100 if valid_e2e else 0
    
    report = {
        "summary": {
            "total_questions": total_q,
            "retrieval_stats": {
                "top_1_recall": top_1_hits / total_q,
                "top_3_recall": top_3_hits / total_q,
                "top_5_recall": top_5_hits / total_q,
                "top_10_recall": top_10_hits / total_q,
                "avg_retrieval_latency_ms": (t_ret_elapsed / total_q) * 1000,
                "total_retrieval_time_sec": t_ret_elapsed,
                "total_translation_time_sec": t_trans_elapsed if 't_trans_elapsed' in locals() else 0.0,
                "total_embedding_time_sec": t_embed_elapsed
            },
            "e2e_stats": {
                "total_e2e_tested": len(valid_e2e),
                "avg_e2e_latency_sec": avg_e2e_latency,
                "language_conformity_rate": conformity_rate,
                "source_match_rate": e2e_source_match_rate,
                "total_e2e_time_sec": t_e2e_all_elapsed
            }
        },
        "file_breakdown": {},
        "retrieval_details": retrieval_results,
        "e2e_details": e2e_results
    }
    
    # format file breakdown
    for f_name, metrics in file_metrics.items():
        f_total = metrics["total"]
        if f_total > 0:
            report["file_breakdown"][f_name] = {
                "total_queries": f_total,
                "top_1_recall": metrics["hit_1"] / f_total,
                "top_3_recall": metrics["hit_3"] / f_total,
                "top_5_recall": metrics["hit_5"] / f_total,
                "top_10_recall": metrics["hit_10"] / f_total,
                "language_conformity": metrics["conformity_passed"] / 1.0 if i % 2 == 0 else 0.0,  # normalized
                "rag_source_match": metrics["e2e_source_passed"] / 1.0,
                "avg_e2e_latency": metrics["total_latency"] / max(1, metrics["e2e_source_passed"] + metrics["conformity_passed"])  # avg over active e2e runs for this file
            }
            
    report_path = Path("c:/cg-eproc-chatbot/scripts/evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"\n💾 Full evaluation report saved successfully to {report_path.name}")
    print("=" * 80)

if __name__ == "__main__":
    run_evaluation()
