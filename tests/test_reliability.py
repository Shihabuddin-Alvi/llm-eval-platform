"""
Phase 5 tests.

Disjointness check: no gold set item overlaps with any Phase 4 probe seed
file. Integrity checks: every gold item has a real human label, and the
labeled correct/incorrect split isn't degenerate.
"""

from pathlib import Path

from core.probes import load_jsonl, PROBE_DIR

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLD_PATH = REPO_ROOT / "data" / "gold" / "gold_v1.jsonl"

PROBE_FAMILIES = ("verbosity", "formatting", "position", "self_preference")


def _gold_rows():
    return load_jsonl(GOLD_PATH)


def _all_probe_inputs():
    inputs = set()
    for name in PROBE_FAMILIES:
        for row in load_jsonl(PROBE_DIR / f"{name}.jsonl"):
            inputs.add(row["input"])
    return inputs


def test_gold_set_disjoint_from_probe_seeds():
    gold_inputs = {row["input"] for row in _gold_rows()}
    probe_inputs = _all_probe_inputs()
    overlap = gold_inputs & probe_inputs
    assert not overlap, (
        f"gold set shares {len(overlap)} question(s) with Phase 4 probe seeds, "
        f"must be held out: {sorted(overlap)}"
    )


def test_gold_set_fully_labeled():
    rows = _gold_rows()
    unlabeled = [r["id"] for r in rows if r["correct"] is None]
    assert not unlabeled, f"gold items missing human labels: {unlabeled}"


def test_gold_set_labels_not_degenerate():
    rows = _gold_rows()
    correct = sum(1 for r in rows if r["correct"])
    incorrect = len(rows) - correct
    assert correct > 0 and incorrect > 0, (
        "gold set labels are all one class, kappa is undefined on a "
        "degenerate label distribution"
    )


def test_gold_set_meets_minimum_size():
    rows = _gold_rows()
    assert len(rows) >= 60, f"gold set has only {len(rows)} items, expected at least 60"