import json

GOLD_PATH = "data/gold/gold_v1.jsonl"

rows = [json.loads(l) for l in open(GOLD_PATH)]
print(f"before dedup: {len(rows)} rows")

seen = set()
deduped = []
for r in rows:
    key = (r["input"], r["prediction"])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(r)

print(f"after dedup: {len(deduped)} rows")

with open(GOLD_PATH, "w") as f:
    for r in deduped:
        f.write(json.dumps(r) + "\n")

print(f"wrote {len(deduped)} rows to {GOLD_PATH}")