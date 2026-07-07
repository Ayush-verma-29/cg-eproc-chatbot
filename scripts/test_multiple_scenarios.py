# scripts/test_multiple_scenarios.py
import sys
import time
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Reconfigure stdout/stderr encoding for Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from app.core.rag_engine import get_rag_engine
from app.core.config import settings

def run_tests():
    # Force settings translation model to Sarvam-1 for this evaluation
    settings.TRANSLATION_MODEL = "mashriram/sarvam-1"
    
    print("==================================================")
    print(f"RAG Chatbot Evaluation (Translation: {settings.TRANSLATION_MODEL})")
    print("==================================================")
    
    scenarios = [
        {
            "role": "vendor",
            "lang": "English",
            "question": "What is the procedure for vendor registration on the Chhattisgarh e-Procurement Portal?"
        },
        {
            "role": "vendor",
            "lang": "Hindi",
            "question": "सुरक्षा निधि (EMD) छूट के लिए कौन सी व्यावसायिक संस्थाएं पात्र हैं?"
        },
        {
            "role": "government_officer",
            "lang": "English",
            "question": "What is the maximum limit for limited tendering under GFR 2017 and how many suppliers are required?"
        },
        {
            "role": "government_officer",
            "lang": "Hindi",
            "question": "शॉर्ट टेंडर नोटिस के नियम क्या हैं?"
        }
    ]
    
    rag_engine = get_rag_engine()
    session_id = "test_eval_session"
    
    report_content = []
    report_content.append("==================================================")
    report_content.append("RAG SYSTEM EVALUATION REPORT")
    report_content.append(f"Translation Model: {settings.TRANSLATION_MODEL}")
    report_content.append(f"LLM Model: {settings.LLM_MODEL}")
    report_content.append("==================================================\n")
    
    for idx, scenario in enumerate(scenarios):
        role = scenario["role"]
        lang = scenario["lang"]
        q = scenario["question"]
        
        print(f"\n[{idx+1}/{len(scenarios)}] Testing Scenario:")
        print(f"   Role: {role.upper()}")
        print(f"   Language: {lang}")
        print(f"   Query: {q}")
        
        start_time = time.time()
        stream = rag_engine.ask_stream(question=q, role=role, session_id=session_id)
        
        full_answer = ""
        metadata_received = None
        
        for event in stream:
            if event["type"] == "start":
                metadata_received = event
            elif event["type"] == "token":
                full_answer += event["text"]
                # Print token to console in real-time
                print(event["text"], end="", flush=True)
            elif event["type"] == "replace":
                full_answer = event["text"]
                
        elapsed = time.time() - start_time
        print(f"\n   Time taken: {elapsed:.2f} seconds")
        print("-" * 50)
        
        # Accumulate report data
        report_content.append(f"SCENARIO {idx+1}:")
        report_content.append(f"Role: {role.upper()}")
        report_content.append(f"Query Language: {lang}")
        report_content.append(f"Question: {q}")
        if metadata_received:
            report_content.append(f"Detected Language: {metadata_received.get('detected_language')}")
            report_content.append(f"Sources Cited: {', '.join(metadata_received.get('sources', []))}")
            report_content.append(f"Rule Citations: {', '.join(metadata_received.get('rule_citations', []))}")
        report_content.append(f"Elapsed Time: {elapsed:.2f} seconds")
        report_content.append("Answer:")
        report_content.append(full_answer)
        report_content.append("\n" + "=" * 50 + "\n")
        
    # Write to report file
    report_path = Path("scripts/scenarios_test_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    print(f"\nEvaluation complete. Full report written to {report_path.resolve()}")

if __name__ == "__main__":
    run_tests()
