# Criterion — LLM Evaluation Platform

A REST API and MCP server for evaluating LLM outputs. Agents call the API programmatically to run evals, compare models, and diagnose failures. The Streamlit UI is a thin wrapper that calls the same API.

**The API is the product. Business logic never lives in the UI layer.**

## Live URLs
- API: https://criterion-api-c7mf.onrender.com
- API docs: https://criterion-api-c7mf.onrender.com/docs
- UI: https://criterion-evall.streamlit.app
- GitHub: https://github.com/Shihabuddin-Alvi/llm-eval-platform

## Stack
- FastAPI: REST API layer
- PostgreSQL: persistence (Render Postgres), pooled via `psycopg2.ThreadedConnectionPool`
- Redis + RQ: async job queue, with a `BackgroundTasks` fallback if Redis is unreachable
- Streamlit: UI layer
- Gemini (`gemini-3.1-flash-lite`): primary LLM judge
- Groq (`llama-3.1-8b-instant`): fallback LLM judge
- TF-IDF + KMeans: failure clustering
- MCP (FastMCP): agent-facing tool server
- Render: API + Postgres hosting
- Streamlit Cloud: UI deployment

## Authentication
All endpoints except `/health` require a Bearer token.

```bash
curl -H "Authorization: Bearer <your-token>" https://criterion-api-c7mf.onrender.com/history
```

## API Endpoints

| Endpoint | Description |
|---|---|
| POST /jobs | Submit single eval, returns result |
| POST /jobs/batch | Submit list of EvalJob objects |
| POST /jobs/upload | Upload CSV or JSONL for batch eval |
| POST /jobs/eval/async | Submit async eval, returns job_id immediately |
| GET /jobs/eval/{job_id} | Poll async job result |
| GET /jobs/{job_id} | Get single job by ID |
| GET /jobs/leaderboard | Models ranked by avg score |
| POST /jobs/failures/cluster | Cluster failure texts |
| POST /jobs/compare | Pairwise comparison between two model outputs |
| DELETE /jobs/cleanup | Delete rows by model_name (defaults to a built-in test-data list if none given) |
| POST /datasets | Create a named eval dataset |
| GET /datasets | List datasets |
| GET /datasets/{id} | Get one dataset |
| POST /datasets/{id}/run | Run an eval experiment over a dataset |
| GET /datasets/experiments | List past experiment runs |
| POST /grade/exact-match | Legacy single-grader route (not under `/jobs`) |
| GET /history | Recent eval results |
| GET /health | Health check |

## Graders
- `exact_match`: strips, lowercases, compares prediction == reference
- `contains_match`: checks if reference appears in prediction
- `regex_match`: re.search with re.DOTALL | re.IGNORECASE
- `llm_judge`: Gemini → Groq → contains_match fallback chain (each tier raises, not returns, to trigger the next)

## MCP Tools
- `run_eval`: calls POST /jobs
- `get_leaderboard`: calls GET /jobs/leaderboard
- `get_clusters`: calls POST /jobs/failures/cluster

Datasets, experiments, pairwise comparison, file upload, and async eval are not currently exposed as MCP tools.

## Streamlit Pages
1. Submit Evaluation
2. History
3. Leaderboard
4. Failure Clusters
5. Upload File
6. Datasets
7. Experiments

## Running Locally

```bash
git clone https://github.com/Shihabuddin-Alvi/llm-eval-platform.git
cd llm-eval-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
CRITERION_API_KEY=your_key
DATABASE_URL=your_postgres_connection_string
REDIS_URL=your_redis_connection_string


The async eval path (`POST /jobs/eval/async`) needs Redis and a running worker to actually process jobs through RQ. Without both, it silently falls back to FastAPI's `BackgroundTasks`, which works but degrades badly under concurrent load (see `docs/phase6_cost_latency.md`). To run the full stack locally:

```bash
redis-server                                # Tab 1 (or your platform's Redis start command)
python3 scripts/worker.py                   # Tab 2 — RQ worker
uvicorn api.main:app --reload                # Tab 3 — API
streamlit run ui/app.py                      # Tab 4 — UI
python3 mcp/server.py                        # Tab 5 — MCP server
```

## Test Suite

Two separate suites, for two separate purposes:

- **`pytest tests/`** — hermetic unit and regression tests, some skip automatically if `DATABASE_URL`/`REDIS_URL` aren't set. Verified passing: **27/27** as of 2026-07-31.
- **`python3 criterion_tests_v3.py`** — a live-integration script that hits the deployed Render URL and needs real API keys and a reachable deployment. It prints its own count only when actually run against a live target; that number is not independently reproducible from the repo alone and is intentionally not restated here as a fixed figure.

## Version

Current tag: `v3.2-phase6`. `/health` reports the real version string, not a stale placeholder.

Post-v3.0, this project went through a structured audit and a phased validation roadmap rather than adding new features blind:

- **Phase 4** — judge bias probe suite (verbosity, position, self-preference, formatting). See `docs/phase4_judge_bias.md`.
- **Phase 5** — calibration and inter-rater reliability against a human-labeled gold set. κ(Gemini, human) = 0.928. See `docs/phase5_reliability.md`.
- **Phase 6** — connection pooling, a real working RQ async worker, load testing, and a cost model. See `docs/phase6_cost_latency.md`.
- **Phase 7** — this documentation and hygiene pass, plus `docs/comparison_frameworks.md`.

A tangible production incident (an expired free-tier database and stale API keys) is documented in full in `docs/incidents/`.
