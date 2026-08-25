import sys
import os
from pathlib import Path

# Ensure UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

TEST_QUESTIONS = [
    "What are the temple opening and closing timings?",
    "How do I travel from Tirupati to Tirumala?",
    "What is the current queue status?",
    "When is the best time to join the queue?",
    "What dress should I wear for darshan?",
    "Where can I get free food?",
    "What is Python?",
    "Explain machine learning simply."
]

def run_tests():
    print("=" * 60)
    print("STARTING AI ASSISTANT END-TO-END VERIFICATION")
    print("=" * 60)
    
    # 1. Health check
    health_res = client.get("/api/health")
    print(f"Health Check: Status={health_res.status_code}, Body={health_res.json()}")
    assert health_res.status_code == 200
    
    # 2. Test each question
    all_passed = True
    for i, q in enumerate(TEST_QUESTIONS, 1):
        print("\n" + "-" * 50)
        print(f"[{i}/{len(TEST_QUESTIONS)}] QUESTION: {q}")
        res = client.post("/api/ai/chat", json={"message": q, "language": "English"})
        if res.status_code == 200:
            data = res.json()
            success = data.get("success")
            answer = data.get("answer") or data.get("reply")
            source = data.get("source")
            print(f"STATUS: {res.status_code} | SUCCESS: {success} | SOURCE: {source}")
            print(f"ANSWER:\n{answer}")
            if not success or not answer:
                all_passed = False
        else:
            print(f"FAILED with status: {res.status_code}, response: {res.text}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL 8 QUESTIONS PASSED SUCCESSFULLY VIA GEMINI!")
    else:
        print("SOME QUESTIONS FAILED.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
