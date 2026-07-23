import requests
import json
import sys

# Configure UTF-8 encoding for safety on Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8001/api/v1"

def run_chat_test():
    print("=" * 60)
    # Step 1: Start session
    print("Starting session with role 'government_officer'...")
    start_payload = {"role": "government_officer"}
    try:
        r = requests.post(f"{BASE_URL}/start", json=start_payload)
        r.raise_for_status()
        start_res = r.json()
        session_id = start_res["session_id"]
        role = start_res["role"]
        print(f"Session started successfully. ID: {session_id}, Role: {role}")
    except Exception as e:
        print(f"Failed to start session: {e}")
        return

    # Step 2: Test general Hinglish query from CG Store Purchase Rules
    test_queries = [
        "Repeat purchase order ki maximum quantity limit kya hai?",
        "Proprietary item kharidne ki maximum value limit kya hai?",
        "Security deposit (EMD) kitna percentage hona chahiye Chhattisgarh Rules ke mutabik?"
    ]

    for query in test_queries:
        print("\n" + "-" * 50)
        print(f"Query: '{query}'")
        print("-" * 50)
        
        chat_payload = {
            "question": query,
            "session_id": session_id
        }
        
        try:
            # Server returns EventSource (SSE) stream
            r = requests.post(f"{BASE_URL}/chat", json=chat_payload, stream=True)
            r.raise_for_status()
            
            print("Response stream: ", end="", flush=True)
            for line in r.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_json = json.loads(line_str[6:])
                        if data_json["type"] == "token":
                            print(data_json["text"], end="", flush=True)
            print()
        except Exception as e:
            print(f"\nFailed to query chat API: {e}")

if __name__ == "__main__":
    run_chat_test()
