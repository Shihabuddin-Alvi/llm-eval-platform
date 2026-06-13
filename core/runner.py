import os
import psycopg2
import psycopg2.extras
from core.models import EvalJob
from core.graders import exact_match, contains_match, regex_match, llm_judge

GRADERS = {
    "exact_match": exact_match,
    "contains_match": contains_match,
    "regex_match": regex_match,
    "llm_judge": llm_judge,
}

def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            input TEXT,
            prediction TEXT,
            reference TEXT,
            grader_name TEXT,
            model_name TEXT,
            score REAL,
            passed INTEGER,
            reasoning TEXT,
            status TEXT DEFAULT 'done',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dataset_items (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
            input TEXT,
            prediction TEXT,
            reference TEXT,
            grader_name TEXT DEFAULT 'exact_match',
            model_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_async_job(job) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO jobs (input, prediction, reference, grader_name, model_name, score, passed, reasoning, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (job.input, job.prediction, job.reference, job.grader_name,
         job.model_name, None, None, None, "pending")
    )
    job_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return job_id

def update_job_with_result(job_id: int, result: dict):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE jobs SET score=%s, passed=%s, reasoning=%s, status=%s
           WHERE id=%s""",
        (result["score"], int(result["passed"]), result.get("reasoning", ""), "done", job_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def save_job_result(job: EvalJob, result: dict) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (input, prediction, reference, grader_name, model_name, score, passed, reasoning)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
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
    job_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return job_id

def load_job_history(limit: int = 50) -> list:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def run_eval(job: EvalJob) -> dict:
    grader_fn = GRADERS.get(job.grader_name)
    if grader_fn is None:
        return {"score": 0.0, "passed": False, "grader": job.grader_name, "reasoning": "Grader not found"}
    result = grader_fn(job.prediction, job.reference)
    job_id = save_job_result(job, result)
    result["id"] = job_id
    return result

def create_dataset(name: str, description: str, items: list) -> dict:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO datasets (name, description) VALUES (%s, %s) RETURNING id, name, description, created_at",
        (name, description)
    )
    row = cur.fetchone()
    dataset_id = row[0]
    for item in items:
        cur.execute(
            """INSERT INTO dataset_items (dataset_id, input, prediction, reference, grader_name, model_name)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (dataset_id, item.get("input", ""), item.get("prediction", ""),
             item.get("reference", ""), item.get("grader_name", "exact_match"),
             item.get("model_name", "unknown"))
        )
    conn.commit()
    cur.close()
    conn.close()
    return {"id": row[0], "name": row[1], "description": row[2], "created_at": str(row[3]), "item_count": len(items)}

def get_datasets() -> list:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT d.id, d.name, d.description, d.created_at, COUNT(di.id) as item_count
        FROM datasets d
        LEFT JOIN dataset_items di ON d.id = di.dataset_id
        GROUP BY d.id
        ORDER BY d.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_dataset(dataset_id: int) -> dict:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
    dataset = cur.fetchone()
    if dataset is None:
        cur.close()
        conn.close()
        return None
    cur.execute("SELECT * FROM dataset_items WHERE dataset_id = %s", (dataset_id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    result = dict(dataset)
    result["items"] = [dict(i) for i in items]
    return result