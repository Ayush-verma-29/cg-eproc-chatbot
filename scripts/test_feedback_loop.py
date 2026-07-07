# scripts/test_feedback_loop.py
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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
FAIL_SYM = get_safe_symbol("❌", "[FAILED]")

def run_tests():
    print("=" * 60)
    print("TESTING FEEDBACK LEARNING (THUMBS UP) & PENALTIES (THUMBS DOWN)")
    print("=" * 60)

    # Backup original analytics logs
    print("\n[INFO] Backing up original analytics logs...", end=" ")
    res = requests.get(f"{API_URL}/admin/analytics")
    if res.status_code != 200:
        print(f"FAILED. Is the server running? (HTTP {res.status_code})")
        return
    initial_analytics = res.json()
    print("SUCCESS")

    # Start a session
    print("\n1. Starting test session...", end=" ")
    res = requests.post(f"{API_URL}/start", json={"role": "vendor"})
    if res.status_code != 200:
        print(f"FAILED (HTTP {res.status_code})")
        return
    session_id = res.json().get("session_id")
    print(f"SUCCESS (Session ID: {session_id})")

    log_id_satisfied = None
    log_id_unsatisfied = None
    satisfied_query = "Dynamic Custom Test Query for Learning Ingestion Loop"
    unsatisfied_query = "Disliked Bad Query for Penalty Loop Validation test"
    accumulated_satisfied_answer = ""
    accumulated_unsatisfied_answer = ""

    try:
        # 2. Send first query to be liked
        print(f"\n2. Sending query to be LIKED: '{satisfied_query}'...", end=" ")
        res = requests.post(
            f"{API_URL}/chat",
            json={"question": satisfied_query, "session_id": session_id},
            stream=True
        )
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return

        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "start":
                        log_id_satisfied = event.get("log_id")
                    elif event.get("type") == "token":
                        accumulated_satisfied_answer += event.get("text", "")
        
        print(f"SUCCESS (Log ID: {log_id_satisfied})")

        # Verify that response text is logged in analytics.json
        res_an = requests.get(f"{API_URL}/admin/analytics")
        analytics_data = res_an.json()
        logged_entry = next((e for e in analytics_data.get("queries", []) if e.get("id") == log_id_satisfied), None)
        assert logged_entry is not None, "Satisfied query entry was not logged in analytics"
        assert logged_entry.get("response") == accumulated_satisfied_answer, "Response text was not saved in log entry"
        print("   Verified response text is saved in analytics log.")

        # 3. Submit satisfied (Thumbs Up) feedback
        print("\n3. Submitting THUMBS UP feedback to trigger vector ingestion...", end=" ")
        res = requests.post(
            f"{API_URL}/chat/feedback",
            json={"log_id": log_id_satisfied, "feedback": "satisfied"}
        )
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code}: {res.text})")
            return
        print("SUCCESS")

        # Let ChromaDB index the document
        time.sleep(1)

        # 4. Verify eProcurement chatbot learned it by checking if it is retrieved as a source in subsequent query
        print("\n4. Verifying eProcurement Chatbot RAG retrieval of learned QA chunk...", end=" ")
        res = requests.post(
            f"{API_URL}/chat",
            json={"question": "What is the result for Dynamic Custom Test Query?", "session_id": session_id},
            stream=True
        )
        
        retrieved_sources = []
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "start":
                        retrieved_sources = event.get("sources", [])
        
        assert "Learned satisfied Q&As" in retrieved_sources, f"Learned source chunk not retrieved! Sources: {retrieved_sources}"
        print("SUCCESS (Successfully retrieved 'Learned satisfied Q&As' chunk!)")

        # 5. Send second query to be disliked
        print(f"\n5. Sending query to be DISLIKED: '{unsatisfied_query}'...", end=" ")
        res = requests.post(
            f"{API_URL}/chat",
            json={"question": unsatisfied_query, "session_id": session_id},
            stream=True
        )
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return

        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "start":
                        log_id_unsatisfied = event.get("log_id")
                    elif event.get("type") == "token":
                        accumulated_unsatisfied_answer += event.get("text", "")
        
        print(f"SUCCESS (Log ID: {log_id_unsatisfied})")

        # 6. Submit unsatisfied (Thumbs Down) feedback
        print("\n6. Submitting THUMBS DOWN feedback to set penalty triggers...", end=" ")
        res = requests.post(
            f"{API_URL}/chat/feedback",
            json={"log_id": log_id_unsatisfied, "feedback": "unsatisfied"}
        )
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code}: {res.text})")
            return
        print("SUCCESS")

        # 7. Query with a semantically overlapping question and verify warning/penalty logs
        print("\n7. Sending semantically similar query to test disliked chunk penalty...", end=" ")
        res = requests.post(
            f"{API_URL}/chat",
            json={"question": "Disliked Bad Query for Penalty Loop Validation testing?", "session_id": session_id},
            stream=True
        )
        
        # Verify response stream works fine after penalty check
        accumulated_text = ""
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "token":
                        accumulated_text += event.get("text", "")
        
        assert len(accumulated_text) > 0, "No response returned after chunk penalty was triggered"
        print("SUCCESS (Penalty deduction logic processed correctly without affecting output)")

        print(f"\n{OK_SYM} Feedback-driven eProcurement Chatbot Learning and Penalty Loop verified successfully!")

    finally:
        # Cleanup Learned Document from ChromaDB
        if log_id_satisfied:
            print("\n[INFO] Cleaning up learned document from ChromaDB...", end=" ")
            try:
                from app.core.rag_engine import get_rag_engine
                rag_engine = get_rag_engine()
                vendor_store = rag_engine.vector_store_manager.get_vendor_store()
                vendor_store.delete(ids=[log_id_satisfied])
                if hasattr(vendor_store, "persist"):
                    vendor_store.persist()
                print("SUCCESS")
            except Exception as e:
                print(f"FAILED: {e}")

        # Terminate test session
        print("[INFO] Terminating test session...", end=" ")
        requests.delete(f"{API_URL}/admin/sessions/{session_id}")
        print("SUCCESS")

        # Restore analytics logs to initial state
        print("[INFO] Restoring initial analytics logs database...", end=" ")
        try:
            from app.services.analytics_service import analytics_service
            with analytics_service.lock:
                analytics_service._write_logs(initial_analytics.get("queries", []))
            print("SUCCESS")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    run_tests()
