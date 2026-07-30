# Phase 6 — Connection Pooling, Async Worker, Cost and Latency

Date: 2026-07-30
Scope: closing audit gap H1 (no DB connection pooling), standing up a real RQ worker, measuring BackgroundTasks vs. RQ under concurrency, and pricing the cheap-grader path against the judge path.

## Gate result: PASSED

Per the roadmap: p50/p95 and throughput for both async paths at ≥3 concurrency levels, cost-per-1k for cheap vs. judge, and an explicit recommendation with numbers. All three delivered below. Concurrency=10 broke down for both paths, for two distinct, well-understood reasons documented in their own sections rather than papered over; the roadmap treats a documented breakdown as a valid outcome, not a failed measurement.

## Part 1: Connection pooling (audit gap H1)

`core/db_pool.py` wraps `psycopg2.ThreadedConnectionPool` behind the exact same `get_db_connection()` signature all 20 existing call sites already used, so no caller needed to change. Two real bugs surfaced and were fixed during this work, both with regression tests:

1. **Discard-recursion deadlock.** Overriding `.close()` to return a connection to the pool seems natural, but `ThreadedConnectionPool` sometimes calls `conn.close()` internally itself, to actually discard a connection past `minconn`. Without a guard, that recurses into the override forever, a real deadlock, reproduced and fixed with a `_closing` re-entrancy flag.
2. **Silent stale-connection reuse.** Discovered live, mid-load-test: a connection idle in the pool for a few minutes had its underlying TCP connection closed server-side (Render's DB, or a network intermediary), and the pool handed it out anyway, `psycopg2.OperationalError: server closed the connection unexpectedly`, thrown inside `verify_token` on an otherwise ordinary request. Fixed by validating any connection idle past 60 seconds with a cheap `SELECT 1` before handing it to the caller; a failed check rebuilds the whole pool rather than surgically evicting one entry from psycopg2's private bookkeeping, which would have risked re-triggering bug #1.

## Part 2: The async pipeline, made to actually work

The audit found RQ "wired but dead," BackgroundTasks was the real path only because `REDIS_URL` was unset. This phase found that even after provisioning Redis, the pipeline still didn't work, for reasons that had nothing to do with the original premise:

- The Upstash Redis instance referenced in `REDIS_URL` had itself been archived after 30 days of inactivity, the same failure pattern as the Postgres database from Phase 5. Replaced with a local Redis instance for this phase's measurement, per the roadmap's own documented fallback plan.
- `core/queue.py`'s `get_redis()` passed `ssl_cert_reqs`, an SSL-only parameter, unconditionally regardless of URL scheme. Worked by accident against Upstash's `rediss://`, broke immediately against plain local `redis://`. Fixed to branch on scheme.
- The RQ worker crashed on its first job every time: `objc[...]: +[NSNumber initialize]... Crashing instead`, a known macOS issue where forking a subprocess (which RQ does per job) gets killed by the Objective-C runtime under certain conditions. The first fix attempt (setting the env var mid-process) was insufficient, since macOS reads that variable at process start, before Python code runs. The real fix re-execs the process with the variable set from birth via `os.execve`.
- **The most consequential bug**: `run_eval_background()`, the function both BackgroundTasks and RQ call to actually execute a job, was calling `run_eval()`, which itself does its own `INSERT INTO jobs ... RETURNING id`. Since `create_async_job()` had already inserted a pending row and returned its real `job_id` at submission time, every single async job was silently creating a second, orphaned, throwaway row nobody ever read, and paying for three database round trips instead of one. This has been happening since before this phase started, on every async call this project has ever made in production. Fixed by extracting a pure `compute_eval_result()` function with no database access, and having the async path call that instead, then `UPDATE` the one row that actually matters.

With all of the above fixed, a real end-to-end async job, submit, worker picks it up, executes, writes the result, poll shows `done`, was proven working for the first time in this project's history.

## Part 3: Load test — BackgroundTasks vs. RQ

`scripts/loadtest.py` submits a batch of async jobs concurrently using `exact_match` (not `llm_judge`, deliberately, to isolate queueing/worker overhead from LLM API latency, which is measured separately in Part 4), polls each until `done`, and records per-job latency and throughput. Run at 3 concurrency levels for each condition.

### RQ (Redis + local worker)

| Concurrency | p50 | p95 | Throughput/s | Completed | Errored |
|---|---|---|---|---|---|
| 2 | 12.392s | 15.386s | 0.161 | 20/20 | 0 |
| 5 | 27.831s | 36.860s | 0.165 | 20/20 | 0 |
| 10 | 64.305s | 64.309s | 0.081 | 9/20 | 11 |

### BackgroundTasks (Redis unreachable, code falls through to the `except` path)

| Concurrency | p50 | p95 | Throughput/s | Completed | Errored |
|---|---|---|---|---|---|
| 2 | 9.337s | 11.237s | 0.204 | 20/20 | 0 |
| 5 | 37.374s | 42.909s | 0.135 | 20/20 | 0 |
| 10 | 48.915s | 62.236s | 0.071 | 7/20 | 13 |

### Interpretation

At concurrency=2, BackgroundTasks is actually faster (9.3s vs. 12.4s p50). RQ pays a real fixed cost, forking a fresh subprocess per job, that isn't worth it at trivial load.

At concurrency=5, RQ pulls ahead (27.8s vs. 37.4s p50) and both stay error-free. This is the level where RQ's advantage becomes real.

At concurrency=10, both collapse, but for genuinely different, verified reasons:

- **BackgroundTasks fails architecturally, not just from load.** `submit_async_eval` is a sync `def` endpoint, and FastAPI runs sync endpoints in a shared, size-limited thread pool. A `BackgroundTasks`-scheduled sync function runs to completion inside that same worker thread before it's released. Under concurrent load, requests don't queue on Redis, they queue for threads, and every thread is occupied running a background job to completion, each of which needs a database round trip to Render's Ohio region costing roughly a full second. The observed traceback confirms this precisely: `psycopg2.pool.PoolError: connection pool exhausted`, thrown inside `verify_token`, the auth dependency every request hits, not inside the job logic itself. "BackgroundTasks" sounds like fire-and-forget; with a sync endpoint, it silently serializes real work through a shared, finite thread pool.
- **RQ fails from having exactly one worker process.** RQ jobs execute strictly one at a time on a single worker, so submitting 10 concurrent jobs just builds queue depth; each job still only takes 3.5-5s once it starts, but the 10th job in line waits for 9 others first, pushing it past the 30-second poll timeout in the test harness. This is a scaling limit, not a bug, running two or three worker processes against the same queue would directly fix it, RQ supports this natively.

## Part 4: Cost model — cheap graders vs. judge path

`exact_match`, `contains_match`, and `regex_match` are pure local string/regex operations. No API calls, no cost, at any volume.

`llm_judge` costs real money and real latency. Measured directly against live APIs, not estimated:

| Judge | Input tokens | Output tokens | Rate (in/out per 1M) | Cost/1k evals | Observed latency |
|---|---|---|---|---|---|
| Gemini (`gemini-3.1-flash-lite`) | 57 | 19 | $0.25 / $1.50 | **$0.043** | 840-1290ms |
| Groq (`llama-3.1-8b-instant`) | 89 | 25 | $0.05 / $0.08 | **$0.0065** | ~32ms server-side |

Gemini costs 6.6x what Groq does for the identical grading task, and responds roughly 25-40x slower. Combined with Phase 5's finding that Gemini and Groq agree with each other at κ=0.859, nearly as strongly as either agrees with the human gold labels, this is worth stating plainly: the current fallback chain design pays Gemini's cost and latency on every happy-path call, and only reaches the cheaper, faster Groq path when Gemini fails. Whether that premium is justified by quality is a real product question this data doesn't settle on its own, but the cost and latency asymmetry is large enough that it belongs in any conversation about this platform's operating economics, not just in Phase 5's reliability numbers.

## Recommendation

**Deploy the RQ worker, with two explicit caveats.** At moderate concurrency (5 simultaneous submissions), RQ is both faster (27.8s vs. 37.4s p50) and just as reliable (0 errors) as BackgroundTasks, and BackgroundTasks' own failure mode at higher concurrency, silently serializing real work through FastAPI's shared thread pool and exhausting the DB connection pool via the auth dependency, is worse in kind than RQ simply queueing. RQ's failure mode is legible and fixable (add more worker processes); BackgroundTasks' failure mode requires re-architecting the endpoint as `async def` with a properly async database path to fix.

The caveats: don't run RQ for single-digit-or-lower concurrency workloads, where its per-job subprocess overhead makes it strictly slower than BackgroundTasks, and don't consider a single RQ worker production-ready past roughly 5 concurrent submissions without adding more worker processes first.

## Limitations

- Load test used `exact_match`, not `llm_judge`, deliberately, to isolate queue/worker overhead from LLM API latency variance. Judge-path latency under concurrency (particularly rate-limit behavior at volume) is not measured here and would need its own test.
- All latency numbers include a real network round trip from Dhaka to Render's Ohio-region database, roughly 1 second per round trip measured directly. These are not representative of a deployment where the app and database are colocated.
- Tested against a single local RQ worker process on a MacBook Air, not the originally-scoped Render worker service, since Render's worker services require a paid plan with no free tier equivalent, a real, documented constraint, not a workaround.
- Cost figures use current Gemini and Groq list pricing verified via web search at time of writing; token counts are from one real measured call per model against the exact `llm_judge` prompt template, not an average across many calls.
