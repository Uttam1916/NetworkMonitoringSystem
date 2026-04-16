import socket
import threading
import time
from cryptography.fernet import Fernet

import config
import state
import database
from database import insert_rtt

# ---- SOCKET ----
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((config.HOST, config.PORT))

cipher = Fernet(config.KEY)

print(f"[UDP] Server running on {config.HOST}:{config.PORT}")


# ---- HANDLE PACKET ----
def handle_packet(data, addr):
    try:
        recv_time = time.time()

        msg = cipher.decrypt(data).decode()
        node, seq, ts, event, metric, value = msg.split("|")

        seq = int(seq)
        ts = int(ts)

    except:
        return

# ---- RTT from client (correct) ----
    if event == "RTT":
        try:
            insert_rtt(node, seq, float(value) / 1000)
        except:
            pass
    # ---- STATE ----
    with state.lock:
        # packet loss detection
        if node in state.last_seq and seq != state.last_seq[node] + 1:
            state.nodes.setdefault(node, {}).setdefault("loss", 0)
            state.nodes[node]["loss"] += 1

        state.last_seq[node] = seq

        state.nodes[node] = {
            "ip": addr[0],
            "last_seen": ts,
            "last_event": event,
        }

        state.event_counts[event] += 1

    # ---- STORE EVENT ----
    database.insert_event(node, ts, event, metric, value)

    # ---- ACK ----
    try:
        ack = f"ACK|{node}|{seq}|{int(time.time()*1000)}"
        sock.sendto(ack.encode(), addr)
    except:
        pass

    print(f"[RECV] {node} | {event} | {metric}={value}")


# ---- RECEIVER LOOP ----
def receiver():
    while True:
        try:
            data, addr = sock.recvfrom(8192)

            threading.Thread(
                target=handle_packet,
                args=(data, addr),
                daemon=True
            ).start()

        except Exception as e:
            print("[ERROR] receiver:", e)


# ---- PERF COLLECTOR (drives charts) ----
def perf_collector():
    while True:
        try:
            now = int(time.time())

            cur = database.get_db().cursor()

            # ---- events/sec ----
            count = cur.execute(
                "SELECT COUNT(*) FROM events WHERE timestamp >= ?",
                (now - 5,)
            ).fetchone()[0]

            eps = count / 5

            # ---- RTT stats ----
            rtt = database.get_rtt_stats(time.time() - 60)

            # ---- packet loss ----
            total_loss = sum(n.get("loss", 0) for n in state.nodes.values())
            total_seq = sum(state.last_seq.values()) or 1

            loss_pct = (total_loss / total_seq) * 100

            # ---- store snapshot ----
            database.insert_perf(
                rtt["avg"],
                rtt["p99"],
                eps
            )

        except Exception as e:
            print("[PERF ERROR]", e)

        time.sleep(3)


# ---- START THREADS ----
threading.Thread(target=receiver, daemon=True).start()
threading.Thread(target=perf_collector, daemon=True).start()


# ---- MAIN LOOP ----
while True:
    time.sleep(5)

    with state.lock:
        print(
            f"[STAT] nodes={len(state.nodes)} "
            f"events={sum(state.event_counts.values())}"
        )