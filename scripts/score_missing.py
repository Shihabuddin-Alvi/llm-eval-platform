import os
import sys
import time
import json
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.graders import llm_judge_gemini, llm_judge_groq

GOLD_PATH = "data/gold/gold_v1.jsonl"
SCORED_PATH = "data/gold/gold_v1_scored.jsonl"

gold = [json.loads(l) for l in open(GOLD_PATH)]
scored = [json.loads(l) for l in open(SCORED_PATH)]
scored_ids = {e["id"] for e in scored}

to_score = [r for r in gold if r["id"] not in scored_ids]
print(f"scoring {len(to_score)} new items")

new_entries = []
for i, r in enumerate(to_score):
    entry = {"id": r["id"], "input": r["input"], "human_correct": r["correct"]}

    attempt = 0
    while attempt < 3:
        try:
            g = llm_judge_gemini(r["prediction"], r["reference"])
            entry["gemini_score"] = g["score"]
            entry["gemini_passed"] = g["passed"]
            break
        except Exception as e:
            attempt += 1
            wait = 15 * attempt
            print(f"id={r['id']} gemini attempt {attempt} failed: {e}, waiting {wait}s")
            time.sleep(wait)
    else:
        entry["gemini_score"] = None
        entry["gemini_passed"] = None

    try:
        q = llm_judge_groq(r["prediction"], r["reference"])
        entry["groq_score"] = q["score"]
        entry["groq_passed"] = q["passed"]
    except Exception as e:
        entry["groq_score"] = None
        entry["groq_passed"] = None
        print(f"id={r['id']} groq failed: {e}")

    print(f"[{i+1}/{len(to_score)}] id={r['id']} human={r['correct']} gemini={entry['gemini_passed']} groq={entry['groq_passed']}")
    new_entries.append(entry)
    time.sleep(2)

all_scored = scored + new_entries
with open(SCORED_PATH, "w") as f:
    for e in all_scored:
        f.write(json.dumps(e) + "\n")

print(f"done. {len(all_scored)} total scored entries.")