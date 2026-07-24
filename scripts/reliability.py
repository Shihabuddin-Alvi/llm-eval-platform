import os
import time
import json
import random
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.graders import llm_judge_gemini, llm_judge_groq
from sklearn.metrics import cohen_kappa_score
import numpy as np

GOLD_PATH = "data/gold/gold_v1.jsonl"
SCORED_PATH = "data/gold/gold_v1_scored.jsonl"


def load_gold(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def score_all(rows):
    scored = []
    for i, r in enumerate(rows):
        entry = {"id": r["id"], "input": r["input"], "human_correct": r["correct"]}
        try:
            g = llm_judge_gemini(r["prediction"], r["reference"])
            entry["gemini_score"] = g["score"]
            entry["gemini_passed"] = g["passed"]
        except Exception as e:
            entry["gemini_score"] = None
            entry["gemini_passed"] = None
            print(f"[{i+1}/{len(rows)}] gemini failed on id {r['id']}: {e}")
        try:
            q = llm_judge_groq(r["prediction"], r["reference"])
            entry["groq_score"] = q["score"]
            entry["groq_passed"] = q["passed"]
        except Exception as e:
            entry["groq_score"] = None
            entry["groq_passed"] = None
            print(f"[{i+1}/{len(rows)}] groq failed on id {r['id']}: {e}")
        scored.append(entry)
        print(f"[{i+1}/{len(rows)}] id={r['id']} human={r['correct']} gemini={entry['gemini_passed']} groq={entry['groq_passed']}")
        time.sleep(0.5)
    return scored


def bootstrap_kappa(y1, y2, n_boot=1000, seed=42):
    rng = random.Random(seed)
    n = len(y1)
    kappas = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        a = [y1[i] for i in idx]
        b = [y2[i] for i in idx]
        try:
            k = cohen_kappa_score(a, b)
        except Exception:
            continue
        if not np.isnan(k):
            kappas.append(k)
    kappas.sort()
    lo = kappas[int(0.025 * len(kappas))]
    hi = kappas[int(0.975 * len(kappas))]
    return lo, hi


def compute_ece(scores, human, n_bins=10):
    bins = [[] for _ in range(n_bins)]
    for s, h in zip(scores, human):
        b = min(int(s * n_bins), n_bins - 1)
        bins[b].append((s, h))
    ece = 0.0
    n_total = len(scores)
    bin_stats = []
    for b in bins:
        if not b:
            bin_stats.append(None)
            continue
        avg_conf = sum(x[0] for x in b) / len(b)
        avg_acc = sum(1 for x in b if x[1]) / len(b)
        ece += (len(b) / n_total) * abs(avg_conf - avg_acc)
        bin_stats.append((avg_conf, avg_acc, len(b)))
    return ece, bin_stats


def sweep_threshold(scores, human):
    best_t, best_acc = 0.5, -1
    for step in range(21):
        t = round(step * 0.05, 2)
        preds = [1 if s >= t else 0 for s in scores]
        acc = sum(1 for p, h in zip(preds, human) if p == (1 if h else 0)) / len(human)
        if acc > best_acc:
            best_acc = acc
            best_t = t
    return best_t, best_acc


def main():
    rows = load_gold(GOLD_PATH)
    assert all(r["correct"] is not None for r in rows), "gold set has unlabeled items"
    print(f"scoring {len(rows)} gold items with Gemini and Groq directly...")
    scored = score_all(rows)

    with open(SCORED_PATH, "w") as f:
        for e in scored:
            f.write(json.dumps(e) + "\n")

    valid_gemini = [e for e in scored if e["gemini_score"] is not None]
    valid_groq = [e for e in scored if e["groq_score"] is not None]
    valid_both = [e for e in scored if e["gemini_score"] is not None and e["groq_score"] is not None]

    print(f"\ngemini answered {len(valid_gemini)}/{len(scored)}")
    print(f"groq answered {len(valid_groq)}/{len(scored)}")
    print(f"both answered {len(valid_both)}/{len(scored)}")

    human_g = [1 if e["human_correct"] else 0 for e in valid_gemini]
    gem = [1 if e["gemini_passed"] else 0 for e in valid_gemini]
    k_gem_human = cohen_kappa_score(gem, human_g)
    lo_gh, hi_gh = bootstrap_kappa(gem, human_g)

    human_q = [1 if e["human_correct"] else 0 for e in valid_groq]
    grq = [1 if e["groq_passed"] else 0 for e in valid_groq]
    k_groq_human = cohen_kappa_score(grq, human_q)
    lo_qh, hi_qh = bootstrap_kappa(grq, human_q)

    gem_b = [1 if e["gemini_passed"] else 0 for e in valid_both]
    grq_b = [1 if e["groq_passed"] else 0 for e in valid_both]
    k_gem_groq = cohen_kappa_score(gem_b, grq_b)
    lo_gg, hi_gg = bootstrap_kappa(gem_b, grq_b)

    gemini_scores = [e["gemini_score"] for e in valid_gemini]
    ece, bin_stats = compute_ece(gemini_scores, human_g)
    best_t, best_acc = sweep_threshold(gemini_scores, human_g)

    print("\n=== RESULTS ===")
    print(f"kappa(gemini, human) = {k_gem_human:.3f}  95% CI [{lo_gh:.3f}, {hi_gh:.3f}]  n={len(valid_gemini)}")
    print(f"kappa(groq, human)   = {k_groq_human:.3f}  95% CI [{lo_qh:.3f}, {hi_qh:.3f}]  n={len(valid_groq)}")
    print(f"kappa(gemini, groq)  = {k_gem_groq:.3f}  95% CI [{lo_gg:.3f}, {hi_gg:.3f}]  n={len(valid_both)}")
    print(f"ECE (gemini score vs human) = {ece:.3f}")
    print(f"recommended threshold = {best_t}  (agreement {best_acc:.3f}, current hardcoded threshold is 0.5)")


if __name__ == "__main__":
    main()