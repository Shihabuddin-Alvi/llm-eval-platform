import json

def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

rows = load("data/gold/gold_v1.jsonl")

trimmed = []
for i in range(0, len(rows), 5):
    block = rows[i:i+5]
    trimmed.append(block[0])
    trimmed.append(block[3])

for new_id, r in enumerate(trimmed, start=1):
    r["id"] = new_id

with open("data/gold/gold_v1.jsonl", "w") as f:
    for r in trimmed:
        f.write(json.dumps(r) + "\n")

labeled = sum(1 for r in trimmed if r["correct"] is not None)
print(f"trimmed to {len(trimmed)} items. {labeled} already labeled, {len(trimmed)-labeled} left.")