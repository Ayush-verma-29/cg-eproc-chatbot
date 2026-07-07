# scripts/test_embeddings_latency.py
import urllib.request
import json
import time

base_url = "http://localhost:11434"
model = "nomic-embed-text"
text = "What is GFR Rule 170?"

print("=== BENCHMARKING OLLAMA EMBEDDING ENDPOINTS ===")

# Test 1: Legacy /api/embeddings
t_start = time.time()
payload = {"model": model, "prompt": text}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(f"{base_url}/api/embeddings", data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as res:
    out = json.loads(res.read().decode('utf-8'))
    emb_len = len(out.get("embedding", []))
t_legacy = time.time() - t_start
print(f"Legacy /api/embeddings: {t_legacy:.4f}s (Dimensions: {emb_len})")

# Test 2: Modern /api/embed
t_start = time.time()
payload = {"model": model, "input": [text]}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(f"{base_url}/api/embed", data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as res:
    out = json.loads(res.read().decode('utf-8'))
    emb_len = len(out.get("embeddings", [[]])[0])
t_modern = time.time() - t_start
print(f"Modern /api/embed:      {t_modern:.4f}s (Dimensions: {emb_len})")
