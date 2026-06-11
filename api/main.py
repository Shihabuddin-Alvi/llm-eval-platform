from dotenv import load_dotenv
load_dotenv()

import os
import secrets
from fastapi import FastAPI, Depends
from api.routes import graders
from api.routes import jobs
from api.routes import history
from core.runner import create_tables, get_db_connection
from core.auth import verify_token

app = FastAPI(
    title="LLM Eval Platform",
    description="REST API for evaluating LLM outputs.",
    version="0.1.0"
)

def seed_api_key():
    token = os.getenv("CRITERION_API_KEY")
    if not token:
        token = secrets.token_hex(32)
        print(f"\n[CRITERION] No API key in .env. Generated key: {token}\n")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO api_keys (token) VALUES (%s) ON CONFLICT (token) DO NOTHING", (token,))
    conn.commit()
    cur.close()
    conn.close()

@app.on_event("startup")
def startup():
    create_tables()
    seed_api_key()

app.include_router(graders.router, dependencies=[Depends(verify_token)])
app.include_router(jobs.router, dependencies=[Depends(verify_token)])
app.include_router(history.router, dependencies=[Depends(verify_token)])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}