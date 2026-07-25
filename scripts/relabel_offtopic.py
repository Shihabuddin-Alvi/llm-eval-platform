import json

GOLD_PATH = "data/gold/gold_v1.jsonl"
TARGET_IDS = {41, 50, 55, 72, 86}

rows = [json.loads(l) for l in open(GOLD_PATH)]

for r in rows:
    if r["id"] in TARGET_IDS:
        print(f"--- item {r['id']} ---")
        print(f"Q: {r['input']}")
        print(f"Prediction: {r['prediction']}")
        print(f"currently labeled: correct={r['correct']}")
        while True:
            ans = input("Correct? [y/n]: ").strip().lower()
            if ans in ("y", "n"):
                break
            print("type y or n")
        r["correct"] = (ans == "y")
        print()

with open(GOLD_PATH, "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

print("done, gold_v1.jsonl updated")