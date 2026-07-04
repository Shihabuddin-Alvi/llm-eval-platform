"""
Phase 4 tests.

Disjointness check: no probe seed input text appears verbatim in ui/app.py
or criterion_tests_v3.py. Fallback integrity check: if any judge call
silently degrades to contains_match, the summary must flag it, never
report a clean llm_judge.
"""

from pathlib import Path

from core.probes import (
    load_jsonl,
    _summarize_graders,
    PROBE_DIR,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _all_seed_inputs():
    inputs = []
    for name in ("verbosity", "formatting", "position", "self_preference"):
        for row in load_jsonl(PROBE_DIR / f"{name}.jsonl"):
            inputs.append(row["input"])
    return inputs


def test_probe_seeds_disjoint_from_ui_and_live_suite():
    candidates = [
        REPO_ROOT / "ui" / "app.py",
        REPO_ROOT / "criterion_tests_v3.py",
    ]
    haystacks = []
    for path in candidates:
        if path.exists():
            haystacks.append(path.read_text())

    if not haystacks:
        return

    for input_text in _all_seed_inputs():
        for haystack in haystacks:
            assert input_text not in haystack, (
                f"probe seed '{input_text}' found verbatim in a UI or live suite "
                "file, probe seeds must be held out"
            )


def test_probe_seed_counts_meet_gate_minimum():
    for name in ("verbosity", "formatting", "position", "self_preference"):
        rows = load_jsonl(PROBE_DIR / f"{name}.jsonl")
        assert len(rows) >= 40, f"{name} has only {len(rows)} seeds, gate needs 40 or more"


def test_summarize_graders_flags_silent_fallback():
    assert _summarize_graders({"llm_judge"}) == "llm_judge"

    mixed = _summarize_graders({"llm_judge", "contains_match"})
    assert mixed != "llm_judge"
    assert "contains_match" in mixed
