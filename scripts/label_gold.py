import json
import sys
import os

PATH = "data/gold/gold_v1_unlabeled.jsonl"
OUT = "data/gold/gold_v1.jsonl"

def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

def save(rows, path):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

def main():
    src = OUT if os.path.exists(OUT) else PATH
    rows = load(src)

    remaining = [r for r in rows if r["correct"] is None]
    done = len(rows) - len(remaining)
    print(f"{done}/{len(rows)} already labeled. {len(remaining)} left.\n")

    for r in rows:
        if r["correct"] is not None:
            continue
        print(f"--- item {r['id']} ---")
        print(f"Q: {r['input']}")
        print(f"Reference: {r['reference']}")
        print(f"Prediction: {r['prediction']}")
        while True:
            ans = input("Correct? [y/n/q=quit and save]: ").strip().lower()
            if ans in ("y", "n", "q"):
                break
            print("type y, n, or q")
        if ans == "q":
            save(rows, OUT)
            print(f"saved progress to {OUT}")
            sys.exit(0)
        r["correct"] = (ans == "y")
        save(rows, OUT)
        print()

    save(rows, OUT)
    print(f"all done. saved to {OUT}")

if __name__ == "__main__":
    main()