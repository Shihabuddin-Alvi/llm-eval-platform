"""
Phase 4. POST /probes/run runs one bias probe family and saves a summary
row to probe_results. Auth is applied at the include_router call in
api/main.py, matching the pattern used by jobs, graders, history, datasets.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.probes import PROBE_RUNNERS
from core.runner import get_db_connection

router = APIRouter(prefix="/probes", tags=["probes"])


class ProbeRunRequest(BaseModel):
    family: str


@router.post("/run")
def run_probe(req: ProbeRunRequest):
    runner = PROBE_RUNNERS.get(req.family)
    if runner is None:
        raise HTTPException(
            status_code=400,
            detail=f"unknown bias family '{req.family}'. valid: {list(PROBE_RUNNERS)}",
        )

    result = runner()

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO probe_results
                (bias_family, n, flip_rate, ci_low, ci_high, judge_grader_used)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (
                result["bias_family"],
                result["n"],
                result["flip_rate"],
                result["ci_low"],
                result["ci_high"],
                result["judge_grader_used"],
            ),
        )
        row_id, created_at = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    result["id"] = row_id
    result["created_at"] = str(created_at)
    return result
