#!/usr/bin/env python
"""Quick E2E test for Hindi streaming response."""
import requests
import json

try:
    print("Testing /ask endpoint with Hindi query...")
    resp = requests.post('http://localhost:8001/ask', json={
        'question': 'mujhe do laptop kharidna hai 2 lakh tak',
        'role': 'vendor'
    }, timeout=10)
    
    if resp.status_code == 200:
        data = resp.json()
        print('✅ Backend is running and responded.')
        print(f"Detected Language: {data.get('detected_language')}")
        answer = data.get('answer', '')
        print(f"Answer (first 300 chars):\n{answer[:300]}...")
        print(f"\nSources: {data.get('sources', [])}")
        print(f"Rule Citations: {data.get('rule_citations', [])}")
    else:
        print(f'❌ Error: HTTP {resp.status_code}')
        print(resp.text)
except Exception as e:
    print(f'❌ Backend unreachable: {e}')
    print('\n   Start backend manually:')
    print('   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload')
