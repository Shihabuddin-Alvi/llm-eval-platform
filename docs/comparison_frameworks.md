# Criterion vs. OpenAI Evals, Ragas, and DeepEval

Date: 2026-07-31

This isn't a claim that Criterion competes with these on breadth, it doesn't, all three are mature, widely-adopted tools built by teams with far more scope. This is an honest accounting of what design choices Criterion made differently, and what it gave up by making them.

## One clarification before comparing anything

"OpenAI Evals" refers to two different things that are easy to conflate. There's the open-source `openai/evals` GitHub repository: a registry of YAML-defined evals, basic/model-graded/solver-based eval types, and an `oaieval` CLI. That project is still active. Separately, there's OpenAI's *hosted* Evals platform (the dashboard and API product). That hosted platform is being deprecated: it goes read-only on October 31, 2026, and shuts down entirely on November 30, 2026. The comparison below is against the open-source framework, since that's the actual architectural peer to a self-hosted tool like Criterion, not the product being sunset.

## Quick comparison

| | Criterion | OpenAI Evals (OSS) | Ragas | DeepEval |
|---|---|---|---|---|
| Primary shape | Live REST API + MCP server | CLI + registry of YAML evals | Python metric library | Pytest-native test framework |
| Grading approach | 3 deterministic graders + 1 reference-based LLM judge | Basic (deterministic) + model-graded + solver-based | Reference-free, RAG-specific metrics | 50+ metrics, deterministic and LLM-judge (G-Eval, DAG) |
| Reference required | Yes, for `llm_judge` | Depends on eval type | No, reference-free by design | Depends on metric |
| Runs where | Deployed, callable by any agent over HTTP or MCP at runtime | Local CLI run against a registry entry | Imported into your own script/pipeline | Local `pytest`/CI run |
| Judge bias/calibration validated | Yes, own measured κ and flip-rate data (Phases 4-5) | Not a built-in concern, it's a harness | Not applicable, metrics aren't a single swappable judge | Framework reports "explainable scores," but validating your specific judge's bias is on you |
| Custom rubric grading | No, single reference-match prompt only | Model-graded evals support custom prompts | No, fixed metric definitions | Yes, G-Eval (rubric, or explicit steps) and DAG (deterministic decision graphs) |
| Async job queue | Yes, RQ-backed, BackgroundTasks fallback | No, synchronous CLI runs | No, synchronous library calls | No, synchronous test runs (parallelizable via pytest-xdist) |

## OpenAI Evals (open source)

Registry-driven: an eval is a YAML file pointing at a dataset and a grading class, run via `oaieval <eval-name> <model>`. Three eval families: basic (deterministic ground-truth matching, closest analog to Criterion's `exact_match`/`contains_match`/`regex_match`), model-graded (an LLM judges the output, closest analog to `llm_judge`), and solver-based (multi-step, for agentic tasks). Custom evals and completion functions plug in through a documented extension point. It doesn't ship a CI/CD runner of its own, you wire that up yourself.

**Where Criterion differs:** OpenAI Evals is a harness you run, not a service you call. There's no persistent API surface, no MCP tools, nothing another agent can hit over HTTP mid-task the way Criterion's `run_eval` MCP tool works. Criterion trades the registry's breadth of pre-built evals for a live, always-on surface.

## Ragas

An open-source (Apache 2.0), reference-free metric library purpose-built for RAG pipelines: faithfulness, answer relevancy, context precision, and context recall are the four canonical metrics, each computed via LLM-as-judge without needing a labeled ground truth. It also generates synthetic evaluation datasets from a document corpus. It's explicitly a library, not a platform, you bring your own dataset, judge model, and place to view results.

**Where Criterion differs:** Ragas solves a problem Criterion doesn't touch at all, retrieval quality. Criterion's `llm_judge` is reference-based by design, it's told the correct answer and asked whether the prediction matches it; Ragas's whole premise is scoring quality *without* a reference. These aren't competing approaches to the same problem, they're answers to different questions. A RAG-heavy system would likely want something like Ragas for retrieval/grounding *and* something like Criterion for scoring correctness against known-good answers, not one instead of the other.

## DeepEval

Open-source (Apache 2.0, built by Confident AI), pytest-native: `deepeval test run` behaves like `pytest`, with LLMTestCase objects and 50+ built-in metrics spanning RAG, multi-turn conversation, agentic tool-use, safety, and multimodal content. Its rubric-grading story is substantially more developed than Criterion's: G-Eval lets you define scoring criteria in plain English (or explicit step-by-step instructions for reproducibility) and constrain output to specific score bands via `Rubric` objects; DAG offers deterministic, rule-based decision-graph scoring for cases where you don't want LLM judgment at all. Confident AI is a separate, connected commercial layer for collaboration and production monitoring.

**Where Criterion differs:** this is the closest peer in spirit, both care about LLM-judge reliability and both integrate into an engineering workflow, but DeepEval's integration point is your test suite and CI pipeline, while Criterion's is a live API another system calls during or after a run. DeepEval's G-Eval and DAG give real per-criterion, rubric-driven grading; Criterion's `llm_judge` is a single holistic reference-match prompt with no rubric decomposition, exactly the kind of judge the audit's Phase 4 bias probes were built to interrogate (verbosity, position, self-preference, formatting sensitivity). DeepEval's docs describe its scores as "explainable," but Criterion is the only one of the four in this table that has published its own measured agreement numbers (κ against a human-labeled gold set) and bias flip-rates for its specific judge configuration, rather than asserting reliability generically.

## The honest tradeoff

Criterion gave up grader breadth (no rubric decomposition, no RAG-specific reference-free metrics, no registry of pre-built evals, no first-class CI integration) in exchange for two things none of the three others provide out of the box: a live, deployed REST/MCP surface an agent can call at runtime rather than a harness you invoke locally, and a judge whose specific failure modes (bias probes in Phase 4, calibration and inter-rater agreement in Phase 5) have actually been measured and published for this exact deployment, not assumed from the framework's general reputation.
