"""
Phase 7 hygiene tests.

Confirms two fixes: /health reports the real current version instead of
the stale 0.1.0 it shipped with since day one (audit D1), and the dead
GET /jobs stub is actually gone, not just returning an empty list
(audit H2). Gated on DATABASE_URL like the rest of this repo's live
tests, since the app's startup event touches the database on any real
request through TestClient.
"""

import os
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="DATABASE_URL not set, skipping live app tests"
)


def test_health_reports_current_version(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] != "0.1.0", "still reporting the stale day-one version string"
    assert data["version"] == "3.2.0"

def test_get_jobs_stub_removed(client):
    r = client.get("/jobs")
    assert r.status_code == 405, "GET /jobs should be gone (405), not the old stub returning []"
    assert r.json() != []