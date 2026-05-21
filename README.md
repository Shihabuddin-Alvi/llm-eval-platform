# Criterion — LLM Evaluation Platform

A REST API and MCP server for evaluating LLM outputs. Agents call the API programmatically to run evals, compare models, and diagnose failures. The Streamlit UI is a thin wrapper that calls the same API.

**The API is the product. Business logic never lives in the UI layer.**

## Live URLs
- API: https://criterion-api-c7mf.onrender.com
- API docs: https://criterion-api-c7mf.onrender.com/docs
- UI: https://criterion-evall.streamlit.app
- GitHub: https://github.com/Shihabuddin-Alvi/-llm-eval-platform

## Stack
- FastAPI: REST API layer
- SQLite: persistence
- Streamlit: UI layer
- Gemini 2.0 Flash Lite: primary LLM judge
- Groq (llama-3.1-8b-instant): fallback LLM judge
- TF-IDF + KMeans: failure clustering
- MCP (FastMCP): agent-facing tool server
- Render: API deployment
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
| POST /eval/async | Submit async eval, returns job_id immediately |
| GET /eval/{job_id} | Poll async job result |
| GET /jobs/{job_id} | Get single job by ID |
| GET /jobs/leaderboard | Models ranked by avg score |
| POST /jobs/failures/cluster | Cluster failure texts |
| GET /history | Recent eval results |
| GET /health | Health check |

## Graders
- `exact_match`: strips, lowercases, compares prediction == reference
- `contains_match`: checks if reference appears in prediction
- `regex_match`: re.search with re.IGNORECASE
- `llm_judge`: Gemini → Groq → contains_match fallback chain

## MCP Tools
- `run_eval`: calls POST /jobs
- `get_leaderboard`: calls GET /jobs/leaderboard
- `get_clusters`: calls POST /jobs/failures/cluster

## Streamlit Pages
1. Submit Evaluation
2. History
3. Leaderboard
4. Failure Clusters
5. Upload File

## Running Locally

```bash
git clone https://github.com/Shihabuddin-Alvi/-llm-eval-platform.git
cd llm-eval-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
CRITERION_API_KEY=your_key
```

```bash
uvicorn api.main:app --reload    # Tab 1
streamlit run ui/app.py          # Tab 2
python mcp/server.py             # Tab 3
```

## Test Suite

```bash
python3 criterion_tests_v3.py
```

55 tests hitting the live Render URL. Current: 54/55 passing (98.2%).

## Version
v2.0 — bearer token auth, async eval, Groq fallback, CSV/JSONL upload, failure clusters UI, MCP get_clusters tool.
