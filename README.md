# Criterion — LLM Evaluation Platform

A REST API and MCP server for evaluating LLM outputs. Agents call the API programmatically to run evals, compare models, and diagnose failures. The Streamlit UI is a thin wrapper that calls the same API.

## Live URLs
- API: https://criterion-api-c7mf.onrender.com
- UI: https://criterion-evall.streamlit.app
- API docs: https://criterion-api-c7mf.onrender.com/docs

## Stack
- FastAPI: REST API layer
- Streamlit: UI layer
- SQLite: persistence
- Gemini 2.0 Flash Lite: LLM judge grader
- MCP: agent-facing tool server

## Graders
- exact_match: checks if prediction matches reference character for character
- contains_match: checks if reference appears anywhere in prediction
- regex_match: checks if prediction matches a regex pattern
- llm_judge: calls Gemini to score prediction against reference, returns score and reasoning

## API Endpoints

### Submit an eval
POST /jobs
curl -X POST https://criterion-api-c7mf.onrender.com/jobs \
  -H "Content-Type: application/json" \
  -d '{"input": "What is the capital of France?", "prediction": "Paris", "reference": "Paris", "grader_name": "exact_match", "model_name": "gpt-4"}'

### Get leaderboard
GET /jobs/leaderboard
curl https://criterion-api-c7mf.onrender.com/jobs/leaderboard

### Get history
GET /history
curl https://criterion-api-c7mf.onrender.com/history

### Batch eval
POST /jobs/batch

### Cluster failures
POST /jobs/failures/cluster

## Architecture
The API is the product. Streamlit calls the API. Business logic never lives in the UI layer.

## Running locally
git clone https://github.com/Shihabuddin-Alvi/-llm-eval-platform.git
cd llm-eval-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload

Add a .env file with:
GEMINI_API_KEY=your_key_here

## MCP Server
python mcp/server.py

Exposes two tools: run_eval and get_leaderboard. Any MCP-compatible agent can call these directly.

## Version
v1.0 — all endpoints live, deployed to Render and Streamlit Cloud.
