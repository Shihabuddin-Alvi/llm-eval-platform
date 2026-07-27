import os
from redis import Redis
from rq import Queue


def get_redis():
    url = os.environ["REDIS_URL"]
    if url.startswith("rediss://"):
        return Redis.from_url(url, ssl_cert_reqs=None)
    return Redis.from_url(url)


def get_queue():
    return Queue(connection=get_redis())