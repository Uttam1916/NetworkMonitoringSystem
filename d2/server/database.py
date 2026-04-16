import os
import sqlite3
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "events.db")

# ---- CONNECTION ----
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row


def get_db():
    return conn


def get_cursor():
    return conn.cursor()


# ---- INIT ----
def init_db():
    cur = get_cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        node TEXT,
        timestamp INTEGER,
        event TEXT,
        metric TEXT,
        value TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ack_log (
        node TEXT,
        seq INTEGER,
        rtt REAL,
        timestamp REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS perf_history (
        captured_at INTEGER,
        avg_rtt_ms REAL,
        p99_rtt_ms REAL,
        events_per_sec REAL
    )
    """)

    conn.commit()


init_db()

# ------------------------------------------------------------------
# EVENTS
# ------------------------------------------------------------------

def insert_event(node, ts, event, metric, value):
    cur = get_cursor()
    cur.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
        (node, ts, event, metric, value),
    )
    conn.commit()


def get_events(limit=100, node_filter="", event_filter=""):
    cur = get_cursor()

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if node_filter:
        query += " AND node LIKE ?"
        params.append(f"%{node_filter}%")

    if event_filter:
        query += " AND event LIKE ?"
        params.append(f"%{event_filter}%")

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = cur.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_total_event_count():
    cur = get_cursor()
    row = cur.execute("SELECT COUNT(*) as c FROM events").fetchone()
    return row["c"] if row else 0


# ------------------------------------------------------------------
# RTT
# ------------------------------------------------------------------

def insert_rtt(node, seq, rtt):
    cur = get_cursor()
    cur.execute(
        "INSERT INTO ack_log VALUES (?, ?, ?, ?)",
        (node, seq, rtt, time.time()),
    )
    conn.commit()


def get_rtt_stats(since_ts):
    cur = get_cursor()

    rows = cur.execute(
        "SELECT rtt FROM ack_log WHERE timestamp >= ?",
        (since_ts,),
    ).fetchall()

    if not rows:
        return {"avg": 0, "p99": 0}

    values = [r["rtt"] * 1000 for r in rows]
    values.sort()

    avg = sum(values) / len(values)
    p99 = values[int(0.99 * len(values))]

    return {
        "avg": round(avg, 2),
        "p99": round(p99, 2)
    }


# ------------------------------------------------------------------
# PERF HISTORY (for charts)
# ------------------------------------------------------------------

def insert_perf(avg_rtt, p99_rtt, eps):
    cur = get_cursor()
    cur.execute(
        "INSERT INTO perf_history VALUES (?, ?, ?, ?)",
        (int(time.time()), avg_rtt, p99_rtt, eps),
    )
    conn.commit()


def get_perf_history(limit=60):
    cur = get_cursor()
    rows = cur.execute(
        "SELECT * FROM perf_history ORDER BY captured_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    return [dict(r) for r in rows]