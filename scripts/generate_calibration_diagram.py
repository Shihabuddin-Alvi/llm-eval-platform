import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCORED_PATH = "data/gold/gold_v1_scored.jsonl"
OUT_PATH = "assets/phase5_reliability_diagram.png"


def compute_bins(scores, human, n_bins=10):
    bins = [[] for _ in range(n_bins)]
    for s, h in zip(scores, human):
        b = min(int(s * n_bins), n_bins - 1)
        bins[b].append((s, h))
    stats = []
    for b in bins:
        if not b:
            stats.append(None)
            continue
        avg_conf = sum(x[0] for x in b) / len(b)
        avg_acc = sum(1 for x in b if x[1]) / len(b)
        stats.append((avg_conf, avg_acc, len(b)))
    return stats


scored = [json.loads(l) for l in open(SCORED_PATH)]
human = [1 if e["human_correct"] else 0 for e in scored]
gemini_scores = [e["gemini_score"] for e in scored]

bin_stats = compute_bins(gemini_scores, human)

confs = [b[0] for b in bin_stats if b]
accs = [b[1] for b in bin_stats if b]
ns = [b[2] for b in bin_stats if b]

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfect calibration")
sizes = [n * 15 for n in ns]
ax.scatter(confs, accs, s=sizes, color="C0", alpha=0.7, label="Gemini judge (bin size = n)")
for c, a, n in zip(confs, accs, ns):
    ax.annotate(f"n={n}", (c, a), textcoords="offset points", xytext=(8, 4))
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)
ax.set_xlabel("Gemini predicted score (confidence)")
ax.set_ylabel("Actual human-labeled accuracy")
ax.set_title("Phase 5: Judge Calibration (Gemini vs human gold labels)")
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig(OUT_PATH, dpi=150)
print(f"saved {OUT_PATH}")