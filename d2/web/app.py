"""
Web dashboard for Network Monitoring System.
Reads everything from SQLite safely (thread-friendly).
"""

import os
import sys
import time

# ---- path setup ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.join(BASE_DIR, "server")

if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

# ---- imports ----
import database
from config import WEB_PORT, NODE_TIMEOUT
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---- helpers ----

def query_one(sql, params=()):
    cur = database.get_db().cursor()
    return cur.execute(sql, params).fetchone()

def query_all(sql, params=()):
    cur = database.get_db().cursor()
    return cur.execute(sql, params).fetchall()


# ---- routes ----

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/events")
def api_events():
    node_filter  = request.args.get("node", "")
    event_filter = request.args.get("event", "")
    limit        = min(int(request.args.get("limit", 100)), 500)

    return jsonify(database.get_events(limit, node_filter, event_filter))


@app.route("/api/nodes")
def api_nodes():
    cutoff = int(time.time()) - NODE_TIMEOUT

    rows = query_all("""
        SELECT node,
               MAX(timestamp) AS last_seen,
               MAX(event)     AS last_event
        FROM events
        WHERE timestamp >= ?
        GROUP BY node
        ORDER BY last_seen DESC
    """, (cutoff,))

    nodes = []
    for r in rows:
        nodes.append({
            "id": r["node"],
            "last_seen": r["last_seen"],
            "last_event": r["last_event"],
            "status": "UP" if r["last_seen"] >= cutoff else "DOWN"
        })

    return jsonify(nodes)


@app.route("/api/perf")
def api_perf():
    now     = int(time.time())
    since5  = now - 5
    since60 = now - 60

    # events/sec
    eps_row = query_one(
        "SELECT COUNT(*) as c FROM events WHERE timestamp >= ?",
        (since5,)
    )
    eps = round((eps_row["c"] or 0) / 5, 2)

    # active nodes
    nodes_row = query_one(
        "SELECT COUNT(DISTINCT node) as c FROM events WHERE timestamp >= ?",
        (now - NODE_TIMEOUT,)
    )
    active_nodes = nodes_row["c"] or 0

    # total events
    total_row = query_one("SELECT COUNT(*) as c FROM events")
    total = total_row["c"] or 0

    # RTT
    rtt = database.get_rtt_stats(since_ts=time.time() - 60)

    # packet loss
    loss_row = query_one("""
        SELECT AVG(CAST(value AS REAL)) as loss
        FROM events
        WHERE event = 'PACKET_LOSS'
        AND timestamp >= ?
    """, (since60,))
    loss_pct = round(loss_row["loss"] or 0, 2)

    return jsonify({
        "active_nodes":    active_nodes,
        "events_per_sec":  eps,
        "avg_rtt_ms":      rtt["avg"],
        "p99_rtt_ms":      rtt["p99"],
        "packet_loss_pct": loss_pct,
        "total_events":    total,
    })


@app.route("/api/perf/history")
def api_perf_history():
    rows = database.get_perf_history(limit=60)
    rows.reverse()
    return jsonify(rows)


@app.route("/api/rtt")
def api_rtt():
    since = float(request.args.get("since", time.time() - 300))
    return jsonify(database.get_rtt_stats(since_ts=since))


# ---- main ----

if __name__ == "__main__":
    print(f"[WEB] Dashboard running on http://0.0.0.0:{WEB_PORT}")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False, threaded=True)