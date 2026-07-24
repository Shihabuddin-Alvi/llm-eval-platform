import json
import random
from sklearn.metrics import cohen_kappa_score
import numpy as np

SCORED_PATH = "data/gold/gold_v1_scored.jsonl"


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


scored = [json.loads(l) for l in open(SCORED_PATH)]
assert all(e["gemini_score"] is not None for e in scored), "still missing gemini scores"
assert all(e["groq_score"] is not None for e in scored), "still missing groq scores"

human = [1 if e["human_correct"] else 0 for e in scored]
gem = [1 if e["gemini_passed"] else 0 for e in scored]
grq = [1 if e["groq_passed"] else 0 for e in scored]

k_gem_human = cohen_kappa_score(gem, human)
lo_gh, hi_gh = bootstrap_kappa(gem, human)

k_groq_human = cohen_kappa_score(grq, human)
lo_qh, hi_qh = bootstrap_kappa(grq, human)

k_gem_groq = cohen_kappa_score(gem, grq)
lo_gg, hi_gg = bootstrap_kappa(gem, grq)

gemini_scores = [e["gemini_score"] for e in scored]
ece, bin_stats = compute_ece(gemini_scores, human)
best_t, best_acc = sweep_threshold(gemini_scores, human)

print(f"n = {len(scored)} (full set)")
print(f"kappa(gemini, human) = {k_gem_human:.3f}  95% CI [{lo_gh:.3f}, {hi_gh:.3f}]")
print(f"kappa(groq, human)   = {k_groq_human:.3f}  95% CI [{lo_qh:.3f}, {hi_qh:.3f}]")
print(f"kappa(gemini, groq)  = {k_gem_groq:.3f}  95% CI [{lo_gg:.3f}, {hi_gg:.3f}]")
print(f"ECE (gemini score vs human) = {ece:.3f}")
print(f"recommended threshold = {best_t}  (agreement {best_acc:.3f}, current hardcoded threshold is 0.5)")
print()
print("calibration bins (avg_conf, avg_acc, n):")
for i, bs in enumerate(bin_stats):
    if bs:
        print(f"  bin {i}: conf={bs[0]:.2f} acc={bs[1]:.2f} n={bs[2]}")