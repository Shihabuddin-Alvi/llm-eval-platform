# LLM Eval Platform

A REST API for evaluating LLM outputs. Agents call the API to run evals, compare models, and diagnose failures.

## Stack
- FastAPI: REST API layer
- Streamlit: UI layer
- SQLite: persistence
- Ollama + Llama 3.1 8B: local inference
- Gemini 1.5 Flash: primary LLM

## Project Status
- Week 1: Project setup, folder structure, GitHub
- Week 3: Exact match grader, Streamlit UI
- Week 7: Three graders, LLM judge
- Week 10: Multi-model leaderboard
- Week 12: MCP server, deployed to Render

## Running locally
uvicorn api.main:app --reload
