import os
import sys
import time
import json
import statistics
import argparse
import concurrent.futures
import httpx
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "http://localhost:8000"
API_KEY = os.environ["CRITERION_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
POLL_TIMEOUT = 30
POLL_INTERVAL = 1.0


def submit_and_wait(client, label, idx):
    payload = {
        "input": f"loadtest {label} {idx} {time.time()}",
        "prediction": "ok",
        "reference": "ok",
        "grader_name": "exact_match",
        "model_name": f"loadtest-{label}",
    }
    submit_start = time.time()
    try:
        r = client.post(f"{BASE_URL}/jobs/eval/async", json=payload, headers=HEADERS)
        r.raise_for_status()
        job_id = r.json()["job_id"]
    except Exception as e:
        return {"job_id": None, "latency": None, "error": f"submit failed: {e}"}

    while True:
        try:
            r2 = client.get(f"{BASE_URL}/jobs/eval/{job_id}", headers=HEADERS)
            data = r2.json()
        except Exception as e:
            return {"job_id": job_id, "latency": None, "error": f"poll failed: {e}"}
        if data.get("status") == "done":
            return {"job_id": job_id, "latency": time.time() - submit_start, "error": None}
        if time.time() - submit_start > POLL_TIMEOUT:
            return {"job_id": job_id, "latency": None, "error": "timeout"}
        time.sleep(POLL_INTERVAL)


def compute_stats(results, wall_time):
    latencies = [r["latency"] for r in results if r.get("latency") is not None]
    errored = [r for r in results if r.get("latency") is None]
    if not latencies:
        return {"p50": None, "p95": None, "throughput_per_sec": 0, "errored": len(errored), "completed": 0}
    sorted_lat = sorted(latencies)
    p50 = statistics.median(sorted_lat)
    if len(sorted_lat) < 5:
        p95 = sorted_lat[-1]  # not enough samples for a meaningful 95th percentile
    else:
        p95_idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        p95 = sorted_lat[p95_idx]
    throughput = len(latencies) / wall_time if wall_time > 0 else 0
    return {
        "p50": round(p50, 3),
        "p95": round(p95, 3),
        "throughput_per_sec": round(throughput, 3),
        "errored": len(errored),
        "completed": len(latencies),
    }


def run_batch(label, concurrency, total):
    print(f"  running {label} at concurrency={concurrency}, total={total}...")
    results = []
    with httpx.Client(timeout=POLL_TIMEOUT + 5) as client:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            wall_start = time.time()
            futures = [ex.submit(submit_and_wait, client, label, i) for i in range(total)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())
            wall_time = time.time() - wall_start
    stats = compute_stats(results, wall_time)
    stats.update({"label": label, "concurrency": concurrency, "total": total, "wall_time": round(wall_time, 3)})
    print(f"    p50={stats['p50']}s  p95={stats['p95']}s  throughput={stats['throughput_per_sec']}/s  "
          f"completed={stats['completed']}/{total}  errored={stats['errored']}")
    errors = [r["error"] for r in results if r.get("error")]
    if errors:
        print(f"    sample errors: {errors[:3]}")
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["backgroundtasks", "rq"])
    parser.add_argument("--concurrency-levels", default="2,5,10")
    parser.add_argument("--total", type=int, default=20)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    levels = [int(x) for x in args.concurrency_levels.split(",")]
    out_path = args.out or f"data/loadtest_{args.label}.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    all_results = []
    for c in levels:
        stats = run_batch(args.label, c, args.total)
        all_results.append(stats)
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"    (saved progress to {out_path})")

    print(f"done. final results in {out_path}")