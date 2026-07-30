"""
Regression test for a real bug: run_eval_background() called run_eval(),
which internally called save_job_result() and inserted a brand-new,
throwaway row, in addition to the pending row create_async_job() already
made. Every async job was silently leaving an orphaned duplicate row in
the jobs table, and paying for three DB round trips instead of one at
the worker step. Fixed by having the async path call compute_eval_result()
directly, a pure grading function with no DB access, and only ever
UPDATE the original row.
"""

import os
import uuid
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="DATABASE_URL not set, skipping live DB tests"
)


def _count_rows_for_input(marker):
    from core.runner import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE input = %s", (marker,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def test_async_path_inserts_exactly_one_row():
    from core.runner import create_async_job, compute_eval_result, update_job_with_result
    from core.models import EvalJob

    marker = f"dup-check-{uuid.uuid4().hex[:8]}"
    job = EvalJob(input=marker, prediction="ok", reference="ok",
                  grader_name="exact_match", model_name="dup-check")

    job_id = create_async_job(job)
    result = compute_eval_result(job)
    update_job_with_result(job_id, result)

    count = _count_rows_for_input(marker)
    assert count == 1, f"expected exactly 1 row, found {count}, duplicate insert bug may have regressed"


def test_sync_path_still_inserts_exactly_one_row():
    from core.runner import run_eval
    from core.models import EvalJob

    marker = f"sync-check-{uuid.uuid4().hex[:8]}"
    job = EvalJob(input=marker, prediction="ok", reference="ok",
                  grader_name="exact_match", model_name="sync-check")

    run_eval(job)

    count = _count_rows_for_input(marker)
    assert count == 1, f"expected exactly 1 row for sync path, found {count}"