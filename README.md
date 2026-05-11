# LLM Eval Platform (Criterion)

A REST API for evaluating LLM outputs. Agents call the API to run evals, compare models, and diagnose failures.

## Current Status
Week 3 complete. Exact match grader live. Streamlit UI connected to API. Tagged v0.1.

## Stack
- FastAPI: REST API layer
- Streamlit: UI layer
- SQLite: persistence
- Ollama + Llama 3.1 8B: local inference
- Gemini 1.5 Flash: primary LLM

## Milestones
- [x] Week 1: Project setup, folder structure, GitHub
- [x] Week 3: Exact match grader, Streamlit UI, v0.1 tagged
- [ ] Week 7: Three graders, LLM judge, v0.2 tagged
- [ ] Week 10: Multi-model leaderboard, failure clustering
- [ ] Week 12: MCP server, deployed to Render
- [ ] Week 14: Public URL, full documentation

## Running locally
uvicorn api.main:app --reload

## API
Interactive docs at http://localhost:8000/docs when running locally.
