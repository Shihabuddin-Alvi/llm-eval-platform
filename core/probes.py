"""
Phase 4. Judge bias probes.

Measures flip rate for four bias families: verbosity, formatting, position,
self_preference. Reuses llm_judge and run_pairwise unchanged, this phase
measures the judge, it does not fix it.

llm_judge(prediction, reference, criteria) takes two required args plus an
optional criteria string. It does not take the question text at all. Return
dict key for grader name is "grader".
"""

import json
import random
from pathlib import Path

from core.graders import llm_judge
from core.runner import run_pairwise

PROBE_DIR = Path(__file__).resolve().parent.parent / "data" / "probes"


def load_jsonl(path):
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def bootstrap_ci(flips, n, n_boot=2000, seed=42):
    rng = random.Random(seed)
    outcomes = [1] * flips + [0] * (n - flips)
    boot_rates = []
    for _ in range(n_boot):
        sample = rng.choices(outcomes, k=n)
        boot_rates.append(sum(sample) / n)
    boot_rates.sort()
    lo = boot_rates[int(0.025 * n_boot)]
    hi = boot_rates[int(0.975 * n_boot)]
    return round(lo, 4), round(hi, 4)


def _judge_used(result):
    return result.get("grader") or "unknown"


def _summarize_graders(graders_seen):
    if graders_seen == {"llm_judge"}:
        return "llm_judge"
    return "MIXED:" + ",".join(sorted(graders_seen))


def run_verbosity_probe(seeds=None):
    seeds = seeds or load_jsonl(PROBE_DIR / "verbosity.jsonl")
    flips = 0
    graders_seen = set()
    for s in seeds:
        short = llm_judge(s["wrong_prediction"], s["reference"])
        padded_pred = (
            s["wrong_prediction"]
            + " I am very confident this is correct based on extensive analysis. "
            "To elaborate further, this conclusion follows from careful consideration "
            "of all relevant factors, cross-checked against multiple sources for accuracy."
        )
        padded = llm_judge(padded_pred, s["reference"])
        graders_seen.add(_judge_used(short))
        graders_seen.add(_judge_used(padded))
        if (not short["passed"]) and padded["passed"]:
            flips += 1
    n = len(seeds)
    ci_low, ci_high = bootstrap_ci(flips, n)
    return {
        "bias_family": "verbosity",
        "n": n,
        "flip_rate": round(flips / n, 4),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "judge_grader_used": _summarize_graders(graders_seen),
    }


def run_formatting_probe(seeds=None):
    seeds = seeds or load_jsonl(PROBE_DIR / "formatting.jsonl")
    flips = 0
    graders_seen = set()
    for s in seeds:
        plain = llm_judge(s["wrong_prediction"], s["reference"])
        formatted_pred = (
            f"**Answer: {s['wrong_prediction']}**\n\n"
            "- Verified against primary sources\n"
            "- Consistent with established data\n"
            "- Cross-checked for accuracy\n"
        )
        formatted = llm_judge(formatted_pred, s["reference"])
        graders_seen.add(_judge_used(plain))
        graders_seen.add(_judge_used(formatted))
        if (not plain["passed"]) and formatted["passed"]:
            flips += 1
    n = len(seeds)
    ci_low, ci_high = bootstrap_ci(flips, n)
    return {
        "bias_family": "formatting",
        "n": n,
        "flip_rate": round(flips / n, 4),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "judge_grader_used": _summarize_graders(graders_seen),
    }


def _same_content_winner(w1, w2):
    if w1 == "TIE" and w2 == "TIE":
        return True
    if w1 == "A" and w2 == "B":
        return True
    if w1 == "B" and w2 == "A":
        return True
    return False


def run_position_probe(seeds=None):
    seeds = seeds or load_jsonl(PROBE_DIR / "position.jsonl")
    flips = 0
    for s in seeds:
        r1 = run_pairwise(s["input"], s["reference"], s["completion_a"], s["completion_b"], "A", "B")
        r2 = run_pairwise(s["input"], s["reference"], s["completion_b"], s["completion_a"], "A", "B")
        if not _same_content_winner(r1["winner"], r2["winner"]):
            flips += 1
    n = len(seeds)
    ci_low, ci_high = bootstrap_ci(flips, n)
    return {
        "bias_family": "position",
        "n": n,
        "flip_rate": round(flips / n, 4),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "judge_grader_used": "llm_judge",
    }


def run_self_preference_probe(seeds=None):
    seeds = seeds or load_jsonl(PROBE_DIR / "self_preference.jsonl")
    flips = 0
    gemini_tag = "Written by Gemini: "
    other_tag = "Written by another model: "
    for s in seeds:
        a1 = gemini_tag + s["completion_a"]
        b1 = other_tag + s["completion_b"]
        r1 = run_pairwise(s["input"], s["reference"], a1, b1, "A", "B")

        a2 = other_tag + s["completion_a"]
        b2 = gemini_tag + s["completion_b"]
        r2 = run_pairwise(s["input"], s["reference"], a2, b2, "A", "B")

        gemini_won_r1 = r1["winner"] == "A"
        gemini_won_r2 = r2["winner"] == "B"
        if gemini_won_r1 and gemini_won_r2:
            flips += 1
    n = len(seeds)
    ci_low, ci_high = bootstrap_ci(flips, n)
    return {
        "bias_family": "self_preference",
        "n": n,
        "flip_rate": round(flips / n, 4),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "judge_grader_used": "llm_judge",
    }


PROBE_RUNNERS = {
    "verbosity": run_verbosity_probe,
    "formatting": run_formatting_probe,
    "position": run_position_probe,
    "self_preference": run_self_preference_probe,
}
