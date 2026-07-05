# Phase 4 — Judge Bias Probe Results

Date run: 2026-07-05
Commit SHA: ec545e3
Judge under test: Gemini 2.0 Flash Lite (llm_judge / llm_judge_gemini), Groq llama-3.1-8b-instant as fallback only

## Method

Four held-out probe families, 46 pairs each, disjoint from ui/app.py placeholders
and criterion_tests_v3.py. Each family reports a flip rate: the fraction of
pairs where an irrelevant manipulation changed the judge's verdict.

Verbosity: wrong answer, padded with confident filler. Flip means short fails, padded passes.
Formatting: wrong answer, plain vs markdown with bullet evidence. Flip means plain fails, formatted passes.
Position: correct vs incorrect completion, run both orders through run_pairwise. Flip means the judge's pick changes with slot, not content.
Self-preference: two correct paraphrases, one tagged Written by Gemini, tags and position both swapped across two runs. Flip means the judge follows the Gemini label in both arrangements.

## Results

| Family | n | flip rate | 95% CI | judge_grader_used |
|---|---|---|---|---|
| verbosity | 46 | 0.0652 | 0.0 to 0.1522 | llm_judge |
| formatting | 46 | 0.0435 | 0.0 to 0.1087 | llm_judge |
| position | 46 | 0.0 | 0.0 to 0.0 | llm_judge |
| self_preference | 46 | 0.0 | 0.0 to 0.0 | llm_judge |

Every row reads llm_judge. No MIXED contamination in any run.

## Gate

All four families have 46 held-out pairs, above the 40 minimum.
All four flip rates and 95% CIs are committed above.
tests/test_probes.py passes, three tests, disjointness, seed count, fallback integrity.
No MIXED grader contamination in any row.

Gate result: PASS.

## Interpretation

Verbosity shows the largest flip rate at 6.52 percent, with a CI upper bound reaching 15.22 percent. Padding a wrong answer with confident sounding filler measurably increases the odds the judge marks it correct. This is the clearest bias signal in the suite and the one worth prioritizing if any mitigation work follows.

Formatting shows a smaller effect, 4.35 percent, CI upper bound 10.87 percent. Wrapping a wrong answer in markdown and a bullet list of fake evidence has a real but smaller effect than verbosity alone.

Position shows zero flips. The judge picked the same correct completion in both slot orders across all 46 pairs. This result is scoped to pairs where content quality is clearly unequal. It does not clear run_pairwise of order sensitivity on close calls, since a genuinely ambiguous pair was not tested here. run_pairwise still always presents model A first in production with no swap, so this remains an open question for pairs where both completions are similarly strong.

Self-preference shows zero flips. The judge did not prefer content labeled as Gemini authored over content labeled as another model's, in either position or label arrangement. This is a clean negative result under the tested condition, one call per arrangement, and does not rule out subtler self-preference effects under different framing.

## Stretch

Not attempted in this run. Core gate is met, so an adversarial iteration on verbosity, where a generator model tries to raise the flip rate further, is available as follow-up work but was not run today.
