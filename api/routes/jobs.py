from fastapi import APIRouter, HTTPException
from typing import List
from core.models import EvalJob
from fastapi import BackgroundTasks
from core.runner import run_eval, get_db_connection, create_async_job, update_job_with_result
from core.clustering import cluster_failures as do_cluster
from fastapi import UploadFile, File
import csv
import json
import io
import psycopg2.extras

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("")
def submit_job(job: EvalJob):
    result = run_eval(job)
    return result

@router.post("/eval/async")
def submit_async_eval(job: EvalJob, background_tasks: BackgroundTasks):
    job_id = create_async_job(job)
    background_tasks.add_task(run_eval_background, job_id, job)
    return {"job_id": job_id, "status": "pending"}

def run_eval_background(job_id: int, job: EvalJob):
    result = run_eval(job)
    update_job_with_result(job_id, result)

@router.get("/eval/{job_id}")
def get_async_job(job_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row)

@router.get("")
def list_jobs():
    return []

@router.get("/leaderboard")
def get_leaderboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            model_name,
            COUNT(*) as total_runs,
            ROUND(AVG(score)::numeric, 3) as avg_score,
            ROUND((SUM(passed) * 100.0 / COUNT(*))::numeric, 1) as pass_rate
        FROM jobs
        WHERE model_name IS NOT NULL AND model_name != ''
        GROUP BY model_name
        ORDER BY total_runs DESC, avg_score DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/batch")
def submit_batch(jobs: List[EvalJob]):
    return [run_eval(job) for job in jobs]

@router.post("/failures/cluster")
def cluster_failures(texts: List[str], n_clusters: int = 3):
    return do_cluster(texts, n_clusters)

@router.delete("/cleanup")
def cleanup_test_data():
    noise = [
        'concurrency-test', 'batch-100', 'perf-test', 'batch-mixed',
        'mixed-test', 'tie-breaker-test', 'integrity-model', 'edge-test',
        'math-verify-model', 'suite-v3'
    ]
    conn = get_db_connection()
    cur = conn.cursor()
    for name in noise:
        cur.execute("DELETE FROM jobs WHERE model_name = %s", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return {"deleted": noise}

@router.post("/upload")
async def upload_eval_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    jobs = []

    if file.filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            jobs.append(EvalJob(
                input=row.get("input", ""),
                prediction=row["prediction"],
                reference=row["reference"],
                grader_name=row.get("grader_name", "exact_match"),
                model_name=row.get("model_name", "unknown")
            ))
    elif file.filename.endswith(".jsonl"):
        for line in text.strip().split("\n"):
            if line:
                data = json.loads(line)
                jobs.append(EvalJob(**data))
    else:
        raise HTTPException(status_code=400, detail="Only .csv and .jsonl files are supported")

    results = [run_eval(job) for job in jobs]
    return results

@router.get("/{job_id}")
def get_job(job_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row)