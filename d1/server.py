import socket
import ssl
import threading
import time
from collections import defaultdict

HOST = "0.0.0.0"
PORT = 9000

CERT = "cert.pem"
KEY = "key.pem"

nodes = {}
event_counts = defaultdict(int)
last_seq = {}

lock = threading.Lock()


def handle_client(conn, addr):

    global nodes

    print("Client connected:", addr)

    while True:
        try:
            data = conn.recv(4096)

            if not data:
                break

            msg = data.decode()
            node, seq, ts, event, metric, value = msg.split("|")

            seq = int(seq)
            ts = int(ts)

            with lock:

                if node not in nodes:
                    nodes[node] = {}

                if node in last_seq and seq != last_seq[node] + 1:
                    print("Packet loss suspected from", node)

                last_seq[node] = seq

                nodes[node]["ip"] = addr[0]
                nodes[node]["last_seen"] = ts
                nodes[node]["event"] = (event, metric, value)

                event_counts[event] += 1

        except Exception as e:
            print("Client error:", e)
            break

    conn.close()
    print("Client disconnected:", addr)


def dashboard():

    while True:

        time.sleep(3)

        with lock:

            print("\n========= NETWORK DASHBOARD =========")

            now = int(time.time())

            print("\nActive Nodes")

            for node in nodes:

                age = now - nodes[node]["last_seen"]

                status = "ONLINE"
                if age > 10:
                    status = "OFFLINE"

                print(
                    f"{node} | {nodes[node]['ip']} | {status} | {age}s ago"
                )

            print("\nLatest Events")

            for node in nodes:

                event, metric, value = nodes[node]["event"]

                print(f"{node} -> {event} ({metric}={value})")

            print("\nEvent Counts")

            for e in event_counts:
                print(e, ":", event_counts[e])

            print("=====================================")


def start_server():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(5)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT, keyfile=KEY)

    print("Secure monitoring server running on port", PORT)

    threading.Thread(target=dashboard, daemon=True).start()

    while True:

        client, addr = sock.accept()

        secure_conn = context.wrap_socket(client, server_side=True)

        threading.Thread(
            target=handle_client,
            args=(secure_conn, addr),
            daemon=True
        ).start()


start_server()
