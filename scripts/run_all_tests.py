# scripts/run_all_tests.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import requests
import json
import time

START_URL = "http://localhost:8001/api/v1/start"
CHAT_URL = "http://localhost:8001/api/v1/chat"

test_queries = [
    ("प्रदर्शन सुरक्षा क्या होती है और यह क्यों आवश्यक है?", "government_officer", "hi"),
    ("निविदा जारी करने के बाद उसमें संशोधन कैसे किया जा सकता है?", "government_officer", "hi"),
    ("क्या सभी निविदाएं ई-प्रोक्योरमेंट के माध्यम से लेना अनिवार्य है?", "government_officer", "hi"),
    ("What are the acceptable forms of Bid Security?", "government_officer", "en"),
    ("What is Force Majeure and how does it affect contracts?", "government_officer", "en"),
    ("ईएमडी कैसे जमा कर सकते हैं? इसके क्या तरीके हैं?", "vendor", "hi"),
    ("एमएसएमई (लघु उद्योग) को निविदा में क्या विशेष लाभ मिलते हैं?", "vendor", "hi"),
    ("What documents are required for supplier registration?", "vendor", "en"),
    ("How to reset password on the e-procurement portal?", "vendor", "en"),
]

print("=" * 70)
print("RUNNING FRESH TEST QUERIES")
print("=" * 70)

for i, (question, role, lang) in enumerate(test_queries, 1):
    print(f"\n{i}. [{role.upper()}] [{lang.upper()}] {question[:60]}...")
    
    try:
        # Step 1: Start session
        start_resp = requests.post(START_URL, json={"role": role})
        if start_resp.status_code != 200:
            print(f"   ❌ Start Session Error ({start_resp.status_code}): {start_resp.text}")
            continue
        session_id = start_resp.json()["session_id"]
        
        # Step 2: Query chat
        response = requests.post(CHAT_URL, json={"question": question, "session_id": session_id}, stream=True)
        if response.status_code != 200:
            print(f"   ❌ Chat Error ({response.status_code}): {response.text}")
            continue
        
        full_answer = ""
        sources = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    try:
                        parsed = json.loads(line_str[6:])
                        if parsed.get("type") == "token":
                            full_answer += parsed.get("text", "")
                        elif parsed.get("type") == "start":
                            sources = parsed.get("sources", [])
                    except Exception:
                        pass
        
        answer_preview = full_answer[:150].replace("\n", " ")
        print(f"   ✅ {answer_preview}...")
        print(f"   📚 Sources: {sources}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    time.sleep(1)

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)