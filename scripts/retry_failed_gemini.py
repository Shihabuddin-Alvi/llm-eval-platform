import os
import sys
import time
import json
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.graders import llm_judge_gemini

GOLD_PATH = "data/gold/gold_v1.jsonl"
SCORED_PATH = "data/gold/gold_v1_scored.jsonl"

gold = {r["id"]: r for r in (json.loads(l) for l in open(GOLD_PATH))}
scored = [json.loads(l) for l in open(SCORED_PATH)]

to_retry = [e for e in scored if e["gemini_score"] is None]
print(f"retrying {len(to_retry)} items with backoff")

for e in to_retry:
    r = gold[e["id"]]
    attempt = 0
    while attempt < 3:
        try:
            g = llm_judge_gemini(r["prediction"], r["reference"])
            e["gemini_score"] = g["score"]
            e["gemini_passed"] = g["passed"]
            print(f"id={e['id']} recovered: score={g['score']}")
            break
        except Exception as ex:
            attempt += 1
            wait = 15 * attempt
            print(f"id={e['id']} attempt {attempt} failed: {ex}, waiting {wait}s")
            time.sleep(wait)
    time.sleep(3)

with open(SCORED_PATH, "w") as f:
    for e in scored:
        f.write(json.dumps(e) + "\n")

still_missing = sum(1 for e in scored if e["gemini_score"] is None)
print(f"done. {still_missing} still missing gemini scores.")