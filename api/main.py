from dotenv import load_dotenv
load_dotenv()
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("criterion")
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
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)
    log_line = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": latency_ms,
    }
    logger.info(json.dumps(log_line))
    return response

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