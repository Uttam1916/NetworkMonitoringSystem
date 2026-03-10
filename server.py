import socket
import threading
import time
from collections import defaultdict

HOST = "0.0.0.0"
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("Monitoring server running on port", PORT)

# Aggregated statistics
event_counts = defaultdict(int)

# node -> last timestamp
node_last_seen = {}

# node -> last event
node_last_event = {}

# node -> last sequence number
node_last_seq = {}

lock = threading.Lock()


def receive_events():
    while True:
        data, addr = sock.recvfrom(2048)

        try:
            msg = data.decode()
            node, seq, ts, event, metric, value = msg.split("|")
            seq = int(seq)

        except Exception:
            print("Malformed packet:", data)
            continue

        with lock:

            # packet loss detection
            if node in node_last_seq:
                if seq != node_last_seq[node] + 1:
                    print("Packet loss detected from", node)

            node_last_seq[node] = seq

            node_last_seen[node] = int(ts)

            node_last_event[node] = (event, metric, value)

            event_counts[event] += 1


def dashboard():
    while True:

        time.sleep(3)

        with lock:

            print("\n================ NETWORK DASHBOARD ================")

            print("\nActive Nodes")

            now = int(time.time())

            for node in node_last_seen:

                age = now - node_last_seen[node]

                status = "ONLINE"

                if age > 10:
                    status = "OFFLINE"

                print(
                    f"{node} | last seen {age}s ago | status {status}"
                )

            print("\nLatest Node Events")

            for node in node_last_event:

                event, metric, value = node_last_event[node]

                print(
                    f"{node} -> {event} ({metric}={value})"
                )

            print("\nEvent Counts")

            for e in event_counts:
                print(e, ":", event_counts[e])

            print("===================================================\n")


receiver_thread = threading.Thread(target=receive_events)
receiver_thread.daemon = True
receiver_thread.start()

dashboard()