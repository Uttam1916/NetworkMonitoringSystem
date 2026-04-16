import subprocess
import time
import requests
import sys
import csv

CLIENT_FILE = "client.py"
API_URL = "http://127.0.0.1:5000/api/perf"

TESTS = [
    {"clients": 1, "interval": 3},
    {"clients": 5, "interval": 1},
    {"clients": 10, "interval": 0.5},
    {"clients": 20, "interval": 0.3},
]

RUN_TIME = 10   # seconds per test


def start_clients(n):
    procs = []
    for _ in range(n):
        p = subprocess.Popen(
            [sys.executable, CLIENT_FILE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procs.append(p)
    return procs


def stop_clients(procs):
    for p in procs:
        p.terminate()
    time.sleep(1)
    for p in procs:
        if p.poll() is None:
            p.kill()


def get_metrics():
    try:
        return requests.get(API_URL).json()
    except:
        return None


results = []

for test in TESTS:
    print(f"\nRunning test: {test}")

    procs = start_clients(test["clients"])

    print("Stabilizing...")
    time.sleep(RUN_TIME)

    metrics = get_metrics()

    if metrics:
        row = {
            "clients": test["clients"],
            "interval": test["interval"],
            "eps": metrics["events_per_sec"],
            "avg_rtt": metrics["avg_rtt_ms"],
            "p99_rtt": metrics["p99_rtt_ms"],
            "loss": metrics["packet_loss_pct"],
            "total_events": metrics["total_events"]
        }
        results.append(row)
        print("Result:", row)
    else:
        print("Failed to fetch metrics")

    stop_clients(procs)
    time.sleep(3)


# ---- SAVE RESULTS ----
with open("results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print("\nSaved results to results.csv")