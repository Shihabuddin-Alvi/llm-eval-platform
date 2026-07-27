import os
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rq import Worker
from core.queue import get_redis

if __name__ == "__main__":
    worker = Worker(["default"], connection=get_redis())
    print("worker started, listening on queue 'default'...")
    worker.work()