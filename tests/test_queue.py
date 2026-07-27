"""
Phase 6 test for core/queue.py.

Regression test for a real bug: get_redis() always passed ssl_cert_reqs,
an SSL-only parameter, to Redis.from_url() regardless of scheme. That
broke any plain redis:// connection (local Redis, or any non-TLS Redis),
and only ever worked against Upstash's rediss:// URL. Skips if
REDIS_URL isn't set, matching the pattern of the other live-connection
tests in this repo.
"""

import os
import pytest

REDIS_URL = os.environ.get("REDIS_URL")

pytestmark = pytest.mark.skipif(
    not REDIS_URL, reason="REDIS_URL not set, skipping live redis tests"
)


def test_get_redis_connects_regardless_of_scheme():
    from core.queue import get_redis

    r = get_redis()
    assert r.ping() is True


def test_get_queue_returns_working_queue():
    from core.queue import get_queue

    q = get_queue()
    assert q.name == "default"
    # len() must work, not raise, confirming the connection is actually live
    assert isinstance(len(q), int)