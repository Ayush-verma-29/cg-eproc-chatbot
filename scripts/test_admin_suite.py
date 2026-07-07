# scripts/test_admin_suite.py
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
FAIL_SYM = get_safe_symbol("❌", "[FAILED]")

def run_tests():
    print("=" * 60)
    print("TESTING COMPREHENSIVE ADMIN CONTROL SUITE & PDF EXPORTS")
    print("=" * 60)

    # 0. Backup original configuration
    print("\n[INFO] Backing up original admin configuration...", end=" ")
    res = requests.get(f"{API_URL}/admin/config")
    if res.status_code != 200:
        print(f"FAILED to read initial configuration. Is the server running? (HTTP {res.status_code})")
        return
    original_config = res.json()
    print("SUCCESS")

    try:
        # 1. Update config with test parameters, blacklist, QA override, and term glossary
        print("\n1. Updating admin configuration with test rules...", end=" ")
        test_config = original_config.copy()
        
        # Test QA override
        test_config["qa_overrides"] = [
            {"query": "custom test question override query", "answer": "Canned Answer Override Result"}
        ]
        
        # Test Blacklist Rule
        test_config["blacklist_rules"] = [
            {"pattern": ".*hackerpattern.*", "response": "Query blocked by security administrator."}
        ]
        
        # Test Protected Terms
        test_config["protected_terms"] = list(set(test_config.get("protected_terms", []) + ["CUSTOMTERM"]))
        
        # Test engine parameters
        test_config["engine_params"] = {
            "k": 5,
            "max_context_chars": 3500,
            "temperature": 0.2
        }

        res = requests.post(f"{API_URL}/admin/config", json=test_config)
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code}: {res.text})")
            return
        print("SUCCESS")

        # 2. Verify that config updates were persisted
        print("\n2. Fetching configuration to verify persistence...", end=" ")
        res = requests.get(f"{API_URL}/admin/config")
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return
        fetched_config = res.json()
        assert fetched_config["engine_params"]["k"] == 5, "Retrieval depth k did not update"
        assert fetched_config["engine_params"]["temperature"] == 0.2, "LLM temperature did not update"
        assert len(fetched_config["qa_overrides"]) > 0, "QA overrides is empty"
        assert fetched_config["qa_overrides"][0]["query"] == "custom test question override query", "QA override query mismatch"
        assert "CUSTOMTERM" in fetched_config["protected_terms"], "Glossary terms did not update"
        print("SUCCESS (Persisted config matches request)")

        # 3. Create a chat session and test Blacklist rule match (intent check bypass)
        print("\n3. Starting session & testing blacklist block...", end=" ")
        # Create session
        res = requests.post(f"{API_URL}/start", json={"role": "vendor"})
        if res.status_code != 200:
            print(f"FAILED to start session (HTTP {res.status_code})")
            return
        session_id = res.json().get("session_id")
        
        # Query with blacklisted term
        res = requests.post(
            f"{API_URL}/chat",
            json={"question": "Tell me how to use the hackerpattern hack.", "session_id": session_id},
            stream=True
        )
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return

        accumulated_text = ""
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "token":
                        accumulated_text += event.get("text", "")
        
        assert accumulated_text == "Query blocked by security administrator.", f"Blacklist response mismatch: '{accumulated_text}'"
        print("SUCCESS (Query correctly blocked with canned response)")

        # 4. Test QA override matching (bypass LLM)
        print("\n4. Testing QA override query matching...", end=" ")
        res = requests.post(
            f"{API_URL}/chat",
            json={"question": "custom test question override query", "session_id": session_id},
            stream=True
        )
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return

        accumulated_text = ""
        sources = []
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    event = json.loads(decoded_line[6:])
                    if event.get("type") == "start":
                        sources = event.get("sources", [])
                    elif event.get("type") == "token":
                        accumulated_text += event.get("text", "")
        
        assert "Canned Answer Override Result" in accumulated_text, f"QA Override answer mismatch: '{accumulated_text}'"
        assert "Admin Override" in sources, "Override source not annotated"
        print("SUCCESS (QA override matched immediately, bypassing LLM)")

        # 5. List active sessions & terminate a session
        print("\n5. Testing active session retrieval...", end=" ")
        res = requests.get(f"{API_URL}/admin/sessions")
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return
        sessions = res.json()
        assert len(sessions) > 0, "No active sessions found"
        # Find our session
        our_session = next((s for s in sessions if s["session_id"] == session_id), None)
        assert our_session is not None, "Our session is missing from listing"
        print(f"SUCCESS ({len(sessions)} active session(s) logged)")

        print("   Terminating our test session...", end=" ")
        res = requests.delete(f"{API_URL}/admin/sessions/{session_id}")
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return
        print("SUCCESS")

        # Verify session is gone
        res = requests.get(f"{API_URL}/admin/sessions")
        sessions_after = res.json()
        our_session_after = next((s for s in sessions_after if s["session_id"] == session_id), None)
        assert our_session_after is None, "Session kill-switch did not clear session"

        # 6. Test Document Governance (deactivating source document)
        print("\n6. Fetching vector store documents list...", end=" ")
        res = requests.get(f"{API_URL}/admin/documents")
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code})")
            return
        documents = res.json()
        print(f"SUCCESS ({len(documents)} source files registered)")
        
        if documents:
            test_doc = "EDGE_Browser_Setup_V1.0.pdf"
            if test_doc not in documents:
                test_doc = documents[0]
            print(f"   Temporarily deactivating document '{test_doc}'...", end=" ")
            deactivate_config = fetched_config.copy()
            deactivate_config["deactivated_documents"] = [test_doc]
            res = requests.post(f"{API_URL}/admin/config", json=deactivate_config)
            if res.status_code != 200:
                print(f"FAILED (HTTP {res.status_code})")
                return
            print("SUCCESS")

            # Check that query does not retrieve chunks from deactivated document
            print(f"   Validating deactivation filtering in RAG retrieval...", end=" ")
            res_sess = requests.post(f"{API_URL}/start", json={"role": "vendor"})
            new_session_id = res_sess.json().get("session_id")
            
            # Request about edge setup or test doc term
            res = requests.post(
                f"{API_URL}/chat",
                json={"question": f"How do I set up browser? {test_doc}", "session_id": new_session_id},
                stream=True
            )
            
            sources = []
            for line in res.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data: "):
                        event = json.loads(decoded_line[6:])
                        if event.get("type") == "start":
                            sources = event.get("sources", [])
            
            # Terminate new session
            requests.delete(f"{API_URL}/admin/sessions/{new_session_id}")
            
            assert test_doc not in sources, f"Source '{test_doc}' was retrieved even though it was deactivated! Sources: {sources}"
            print("SUCCESS (Excluded from active chunk context)")

        # 7. Test PDF export of analytics report
        print("\n7. Requesting analytics PDF audit report export...", end=" ")
        res = requests.get(f"{API_URL}/admin/export_pdf")
        if res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code}: {res.text})")
            return
        assert res.headers.get("content-type") == "application/pdf", f"Content-type mismatch: {res.headers.get('content-type')}"
        assert len(res.content) > 1000, f"PDF content size is suspiciously small: {len(res.content)} bytes"
        print(f"SUCCESS (Valid PDF stream returned, size: {len(res.content)} bytes)")

        print(f"\n{OK_SYM} All 9 administrative capabilities integration tests passed successfully!")

    finally:
        # Restore original config
        print("\n[INFO] Restoring initial admin configuration...", end=" ")
        res = requests.post(f"{API_URL}/admin/config", json=original_config)
        if res.status_code == 200:
            print("SUCCESS")
        else:
            print(f"FAILED to restore! (HTTP {res.status_code}: {res.text})")

if __name__ == "__main__":
    run_tests()
