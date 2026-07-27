import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.queue import get_redis, get_queue

print("testing Redis connection...")
try:
    r = get_redis()
    pong = r.ping()
    print(f"  connected: {pong}")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

print()
print("checking queue state...")
q = get_queue()
print(f"  queue name: {q.name}")
print(f"  jobs currently queued: {len(q)}")

if len(q) > 0:
    print()
    print("  jobs sitting in queue right now:")
    for job in q.jobs[:10]:
        print(f"    id={job.id} created_at={job.created_at} args={job.args}")