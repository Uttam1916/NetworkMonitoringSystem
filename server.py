import socket
from collections import defaultdict
import time

HOST = "0.0.0.0"
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("Monitoring server running on port", PORT)

event_counts = defaultdict(int)
node_last_seq = {}
node_last_seen = {}

while True:

    data, addr = sock.recvfrom(2048)

    message = data.decode()

    node, seq, ts, event, metric, value = message.split("|")

    seq = int(seq)

    # packet loss detection
    if node in node_last_seq:
        if seq != node_last_seq[node] + 1:
            print("WARNING: packet loss from", node)

    node_last_seq[node] = seq
    node_last_seen[node] = ts

    event_counts[event] += 1

    print("\nEVENT RECEIVED")
    print("Node:", node)
    print("Event:", event)
    print("Metric:", metric)
    print("Value:", value)

    print("\nACTIVE NODES")
    for n in node_last_seen:
        print(n, "last seen", node_last_seen[n])

    print("\nEVENT COUNTS")
    for e in event_counts:
        print(e, ":", event_counts[e])