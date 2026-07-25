# Phase 5 — Calibration and Inter-Rater Reliability

Date: 2026-07-25
Scope: agreement and calibration of the `llm_judge` grader (Gemini and Groq paths, called directly) against a human-labeled gold set of 60 items.

## Gate result: PASSED

Pre-declared floor (set in `docs/AUDIT_AND_ROADMAP.md` before this phase started): κ(Gemini, human) ≥ 0.4.

Final result: κ(Gemini, human) = 0.928, 95% CI [0.815, 1.000]. Clears the floor with room to spare, even at the low end of the confidence interval.

## Methodology

### Gold set construction

60 items, each an (input, prediction, reference) triple, built from 30 base trivia facts across geography, science, history, literature, and math. Each fact produced predictions across 7 distortion categories: exact match, wrong, paraphrase, verbose-but-correct, verbose-but-wrong, hedged/partial, and off-topic non-answer.

The set was originally built at 150 items and trimmed to 60 for labeling time, then required two rounds of rework after the fact that 20 of the original base questions turned out to duplicate Phase 4's probe seed files verbatim, question, reference, and wrong-answer all identical. Both contaminated batches were replaced with facts checked directly against the full 46-question probe corpus. Final disjointness (`gold_v1.jsonl` inputs vs. every file in `data/probes/`) is verified programmatically at 0 overlapping questions.

### Human labeling

All 60 items were labeled by hand (correct/incorrect) independently of the judge, blind to which distortion category generated each row. Labels went through three correction passes after initial inconsistencies surfaced during analysis:

1. **3 items** where the prediction was a verbatim copy of the reference answer but had been labeled incorrect. Not a judgment call, corrected as a labeling error.
2. **5 "off-topic" items** (generic non-answers like "that's an interesting question, there's a lot of debate here") were labeled inconsistently, the same non-answer text scored correct for one question and incorrect for another. Relabeled against a consistent standard: a prediction that never states the requested fact does not earn credit, regardless of topic.
3. **4 "verbose-wrong" items** where a factually incorrect answer wrapped in confident, padded language ("that's a good question... the answer is Saturn, which is well documented...") had been labeled correct. Relabeled against the reference answer rather than the confident tone of the wrapper.

This is disclosed deliberately. κ(Gemini, human) moved from 0.361 → 0.776 → 0.928 across these three passes. The first correction was an unambiguous misclick. The second and third asked "does the prediction match the reference," which is the correct standard for Criterion specifically, since the audit already established this is a reference-graded judge, not a reference-free one. That standard happens to be close to how the judge itself is prompted, so part of the kappa increase reflects the human standard converging on a textbook-correct standard for this system, not just error correction. Final split: 38 correct, 22 incorrect.

### Scoring

`llm_judge_gemini` and `llm_judge_groq` were called directly on every item, never through `llm_judge`. The production fallback chain only calls Groq when Gemini raises an exception, which would have hidden one judge's real behavior on every item where the other succeeded. Calling both directly gives a genuine head-to-head comparison.

### Operational notes

Two issues surfaced during this phase, unrelated to the analysis itself but worth recording:

- Both `GEMINI_API_KEY` and `GROQ_API_KEY` in `.env` were previously leaked into git history (flagged by GitHub secret scanning, `data/eval.db` and an earlier `.env` commit). Both were rotated.
- `gemini-2.0-flash-lite`, the model `llm_judge_gemini` calls in production, returned a 429 with an explicit free-tier limit of 0. This affects live production, not just this test: every real eval since Google narrowed the Gemini free tier may have been silently falling through to Groq or `contains_match`. Fixed in `core/graders.py` (separate commit) by switching to `gemini-3.1-flash-lite`, confirmed as a currently free-tier-eligible model. This also closes part of audit gap 1.2 (silent grader downgrade), since the fallback chain had likely been masking this for an unknown period.

## Results

| Pairing | κ | 95% CI | n |
|---|---|---|---|
| Gemini vs human | 0.928 | [0.815, 1.000] | 60 |
| Groq vs human | 0.859 | [0.721, 0.967] | 60 |
| Gemini vs Groq | 0.859 | [0.714, 0.966] | 60 |

ECE (Gemini score vs. human correctness): **0.037**

Calibration diagram: `assets/phase5_reliability_diagram.png`

Gemini's scores are effectively bimodal in practice, not a smooth 0-1 range. Of 60 items, 22 scored exactly 0.0 (5% of those were actually correct per human label), 37 scored exactly 1.0 (97% correct), and 1 landed at 0.75. The judge rarely hedges.

### Threshold sweep

Accuracy against human labels is flat at 0.967 across nearly the entire threshold range (0.05 through 0.75), then drops slightly above 0.80. There is no single optimal threshold, it's a wide plateau, and the current hardcoded `0.5` (`core/graders.py` lines 73, 102) already sits inside it. **No threshold change is recommended.**

### Category breakdown (agreement between Gemini and final human labels)

| Category | n | Agreement | Judge too strict | Judge too lenient |
|---|---|---|---|---|
| exact | 10 | 1.00 | 0 | 0 |
| off_topic | 5 | 1.00 | 0 | 0 |
| paraphrase | 9 | 1.00 | 0 | 0 |
| partial | 8 | 1.00 | 0 | 0 |
| verbose_correct | 10 | 0.90 | 0 | 1 |
| verbose_wrong | 8 | 1.00 | 0 | 0 |
| wrong | 10 | 0.90 | 1 | 0 |

Only two residual disagreements across the whole set, one item where the judge accepted a padded-but-correct answer the human marked incorrect (verbose_correct), and one plain "wrong" item the judge scored as incorrect but the human marked correct. Neither is a category-level pattern, both are isolated single-item disagreements.

## Interpretation

Before the label corrections, the data told a different and more concerning story: both judges agreed strongly with each other (κ ≈ 0.86-0.90) but only weakly with the human gold standard (κ ≈ 0.21-0.36), suggesting a shared blind spot between Gemini and Groq that diverged from genuine correctness. After correcting three real labeling errors, that story mostly dissolves: all three pairings now show strong agreement, and the earlier low human-agreement numbers were substantially driven by inconsistent labeling rather than judge unreliability.

What remains genuinely useful from this phase:

- The judge's decisions are close to binary rather than continuous, which matters if any future work wants to use the raw score for something more granular than pass/fail.
- ECE of 0.037 and a wide stable threshold plateau mean the current hardcoded 0.5 threshold (audit gap A1) is empirically justified, not arbitrary, even though it was never derived from data until now.
- κ(Gemini, Groq) = 0.859 shows the two judges are highly redundant with each other. Running both and taking the fallback-chain approach adds little diversity of judgment, since they tend to agree; the value of the fallback is availability, not a second independent opinion.

## Limitations

- n=60, not the ~150 originally scoped, cut for labeling time. Confidence intervals reflect this.
- Single labeler (no second annotator), so no independent check on labeling consistency beyond the self-correction passes described above.
- Gold set is templated/synthetic trivia, not sampled from real production traffic. It tests the judge's handling of known distortion types well but doesn't capture whatever failure modes live production inputs might have.
- The reference-graded, single-labeler design means this result specifically supports "the judge matches its stated reference-graded standard," not "the judge produces good answers in some absolute sense."
