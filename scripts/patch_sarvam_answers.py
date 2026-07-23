# scripts/patch_sarvam_answers.py
import os
import sys
import json
import time

# Append scripts folder to sys.path
sys.path.append(os.path.dirname(__file__))
from run_dual_evaluation import generate_markdown_report, generate_pdf_report, call_sarvam
from convert_evaluation_to_docx import create_docx_report

def main():
    json_path = os.path.join(os.path.dirname(__file__), "dual_evaluation_report.json")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    print(f"Loaded {len(results)} results from {json_path}")
    
    local_latencies = []
    sarvam_latencies = []
    patched_count = 0
    
    for idx, r in enumerate(results, 1):
        local_latencies.append(r["local_latency_ms"])
        
        # If the response is reasoning only, we need to re-query with max_tokens=4096
        # Also check if it's 1024 tokens which implies truncation
        if r["sarvam_answer"].startswith("[Reasoning Only Answer]") or r["sarvam_tokens"] == 1024:
            print(f"[{idx:02d}/50] Patching {r['id']} (Reasoning Only / Truncated)...")
            time.sleep(0.5) # prevent rate limit
            res = call_sarvam(r["question"])
            print(f"       Old Latency: {r['sarvam_latency_ms']}ms | New Latency: {res['latency_ms']}ms")
            print(f"       Old Tokens: {r['sarvam_tokens']} | New Tokens: {res['tokens']}")
            
            r["sarvam_answer"] = res["answer"]
            r["sarvam_latency_ms"] = res["latency_ms"]
            r["sarvam_tokens"] = res["tokens"]
            patched_count += 1
        else:
            print(f"[{idx:02d}/50] Keeping {r['id']} (Answer is already clean).")
            
        sarvam_latencies.append(r["sarvam_latency_ms"])
        
    print(f"\nPatched {patched_count} answers.")
    
    # Save back to json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved updated raw results to: {json_path}")
    
    # Regenerate reports
    print("Regenerating Markdown report...")
    generate_markdown_report(results, local_latencies, sarvam_latencies)
    
    print("Regenerating PDF report...")
    generate_pdf_report(results, local_latencies, sarvam_latencies)
    
    print("Regenerating DOCX report...")
    create_docx_report()
    
    print("Patching process completed successfully!")

if __name__ == "__main__":
    main()
