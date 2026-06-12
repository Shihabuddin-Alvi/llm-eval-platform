import os
from redis import Redis
from rq import Queue

def get_redis():
    return Redis.from_url(os.environ["REDIS_URL"], ssl_cert_reqs=None)

def get_queue():
    return Queue(connection=get_redis())