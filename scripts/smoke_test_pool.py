import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.runner import get_db_connection
import core.db_pool as db_pool

print("opening and closing 5 connections in sequence...")
for i in range(5):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    print(f"  [{i+1}/5] query ok, result={result}, pool object id={id(db_pool._pool)}")

print()
print("opening 3 connections at once without closing, to confirm the pool actually hands out separate connections...")
conns = [get_db_connection() for _ in range(3)]
print(f"  got {len(conns)} live connections, ids: {[id(c) for c in conns]}")
for c in conns:
    c.close()
print("closed all 3, returned to pool")

print()
print("SUCCESS: pool is alive and reusable")