# scripts/test_analytics.py
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

API_URL = "http://localhost:8001/api/v1"

def get_safe_symbol(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'ascii')
        return emoji
    except Exception:
        return fallback

OK_SYM = get_safe_symbol("🎉", "[SUCCESS]")

def run_tests():
    print("=" * 60)
    print("TESTING ANALYTICS & FEEDBACK ENDPOINTS")
    print("=" * 60)

    # 1. Start Session
    print("\n1. Starting session...", end=" ")
    res = requests.post(f"{API_URL}/start", json={"role": "vendor"})
    if res.status_code != 200:
        print(f"FAILED (HTTP {res.status_code})")
        return
    session_id = res.json().get("session_id")
    print(f"SUCCESS (Session ID: {session_id})")

    # 2. Call Chat endpoint and read SSE stream to extract log_id
    print("\n2. Sending chat query & reading SSE stream...", end=" ")
    res = requests.post(
        f"{API_URL}/chat",
        json={"question": "What documents are required for vendor registration?", "session_id": session_id},
        stream=True
    )
    if res.status_code != 200:
        print(f"FAILED (HTTP {res.status_code})")
        return

    log_id = None
    accumulated_text = ""
    for line in res.iter_lines():
        if line:
            decoded_line = line.decode('utf-8').strip()
            if decoded_line.startswith("data: "):
                try:
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "start":
                        log_id = event.get("log_id")
                    elif event.get("type") == "token":
                        accumulated_text += event.get("text", "")
                except Exception as e:
                    pass

    if log_id:
        print(f"SUCCESS (Log ID extracted: {log_id})")
        print(f"   Response snippet: {accumulated_text[:100]}...")
    else:
        print("FAILED (Could not extract log_id from SSE stream)")
        return

    # 3. Submit feedback
    print(f"\n3. Submitting feedback for log ID '{log_id}'...", end=" ")
    res = requests.post(
        f"{API_URL}/chat/feedback",
        json={"log_id": log_id, "feedback": "satisfied"}
    )
    if res.status_code != 200:
        print(f"FAILED (HTTP {res.status_code}: {res.text})")
        return
    print("SUCCESS (Feedback recorded)")

    # 4. Fetch admin analytics metrics
    print("\n4. Fetching admin analytics metrics...", end=" ")
    res = requests.get(f"{API_URL}/admin/analytics")
    if res.status_code != 200:
        print(f"FAILED (HTTP {res.status_code}: {res.text})")
        return
    metrics = res.json()
    print("SUCCESS")
    print("-" * 40)
    print(f"Total Queries:      {metrics.get('total_queries')}")
    print(f"Avg Response Time:  {metrics.get('avg_response_time')}s")
    print(f"Satisfaction Rate:  {metrics.get('satisfaction_rate')}%")
    print(f"Most Asked Topics:  {metrics.get('most_asked_topics')}")
    print(f"Recent Queries (showing up to 2):")
    for q in metrics.get("queries", [])[:2]:
        print(f"  - [{q.get('role')}] '{q.get('query')}' | Speed: {q.get('response_time_seconds')}s | Feedback: {q.get('feedback')}")
    print("-" * 40)

    # Simple validations
    assert metrics.get("total_queries", 0) > 0, "Total queries should be > 0"
    assert metrics.get("avg_response_time", 0.0) >= 0.0, "Avg response time should be >= 0.0"
    
    print(f"\n{OK_SYM} All integration checks for Analytics and feedback passed successfully!")

if __name__ == "__main__":
    run_tests()
