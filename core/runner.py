import sqlite3
import os
from core.models import EvalJob
from core.graders import exact_match, contains_match, regex_match, llm_judge

DB_PATH = "data/eval.db"

GRADERS = {
    "exact_match": exact_match,
    "contains_match": contains_match,
    "regex_match": regex_match,
    "llm_judge": llm_judge,
}

def create_tables():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input TEXT,
            prediction TEXT,
            reference TEXT,
            grader_name TEXT,
            model_name TEXT,
            score REAL,
            passed INTEGER,
            reasoning TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_job_result(job: EvalJob, result: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO jobs (input, prediction, reference, grader_name, model_name, score, passed, reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.input,
        job.prediction,
        job.reference,
        job.grader_name,
        job.model_name,
        result.get("score", 0.0),
        1 if result.get("passed") else 0,
        result.get("reasoning", "")
    ))
    conn.commit()
    conn.close()

def load_job_history(limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def run_eval(job: EvalJob) -> dict:
    grader_fn = GRADERS.get(job.grader_name)
    if grader_fn is None:
        return {"score": 0.0, "passed": False, "grader": job.grader_name, "reasoning": "Grader not found"}
    result = grader_fn(job.prediction, job.reference)
    save_job_result(job, result)
    return result