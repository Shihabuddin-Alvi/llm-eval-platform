import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.fork_safety import ensure_fork_safety_env
ensure_fork_safety_env()

from dotenv import load_dotenv
load_dotenv()

from rq import Worker
from core.queue import get_redis

if __name__ == "__main__":
    worker = Worker(["default"], connection=get_redis())
    print("worker started, listening on queue 'default'...")
    worker.work()