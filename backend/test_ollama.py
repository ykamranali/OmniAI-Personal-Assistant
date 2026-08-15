"""
Quick Ollama test script for OmniAI Personal Assistant.
Tests connectivity, lists models, and runs a small chat generation.
"""
import httpx
import json
import sys

BASE = "http://localhost:11434"

def header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}")

# ── 1. Health check ───────────────────────────────────
header("1. Ollama Health Check")
try:
    r = httpx.get(f"{BASE}/api/version", timeout=5)
    data = r.json()
    print(f"  ✅ Ollama is running! Version: {data.get('version', 'unknown')}")
except Exception as e:
    print(f"  ❌ Cannot reach Ollama: {e}")
    sys.exit(1)

# ── 2. List models ────────────────────────────────────
header("2. Available Models")
try:
    r = httpx.get(f"{BASE}/api/tags", timeout=5)
    models = r.json().get("models", [])
    if not models:
        print("  ⚠️  No models found. Run: ollama pull llama3.2")
        sys.exit(1)
    for m in models:
        size_gb = m.get("size", 0) / 1e9
        family  = m.get("details", {}).get("family", "?")
        params  = m.get("details", {}).get("parameter_size", "?")
        print(f"  ✅ {m['name']}  ({params}, {size_gb:.1f} GB, family: {family})")
    test_model = models[0]["name"]
except Exception as e:
    print(f"  ❌ Failed to list models: {e}")
    sys.exit(1)

# ── 3. Chat test ──────────────────────────────────────
header(f"3. Chat Generation Test (using {test_model})")
print(f"  Prompt: 'What is 2+2? Reply in one short sentence.'")
print(f"  Waiting for response...\n")

payload = {
    "model": test_model,
    "messages": [
        {"role": "user", "content": "What is 2+2? Reply in one short sentence."}
    ],
    "stream": False
}

try:
    r = httpx.post(f"{BASE}/api/chat", json=payload, timeout=120)
    data = r.json()
    response_text = data.get("message", {}).get("content", "")
    duration_ns = data.get("total_duration", 0)
    duration_s  = duration_ns / 1e9
    print(f"  Response: {response_text.strip()}")
    print(f"  ⏱️  Generation time: {duration_s:.1f}s")
    print(f"\n  ✅ Chat generation works!")
except Exception as e:
    print(f"  ❌ Chat generation failed: {e}")
    sys.exit(1)

# ── 4. Test via OmniAI backend route ─────────────────
header("4. Test via OmniAI Backend /api/v1/models/")
try:
    r = httpx.get("http://localhost:8000/api/v1/models/", timeout=10)
    data = r.json()
    count = len(data.get("data", []))
    print(f"  ✅ OmniAI backend sees {count} Ollama model(s)")
    for m in data.get("data", []):
        print(f"     - {m.get('name', '?')}")
except Exception as e:
    print(f"  ❌ Could not reach OmniAI backend: {e}")

# ── Summary ───────────────────────────────────────────
header("Summary")
print(f"  Ollama: ✅ Online")
print(f"  Models: {len(models)} available")
print(f"  Chat:   ✅ Working")
print(f"\n  Default model in OmniAI: llama3.1")
print(f"  Test model used:         {test_model}")
print()
