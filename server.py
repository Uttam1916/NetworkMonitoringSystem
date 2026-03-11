import socket

HOST = "0.0.0.0"
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("Monitoring server started on port", PORT)

# Aggregated event counters
latency_events = 0
failure_events = 0
performance_events = 0

while True:

    data, addr = sock.recvfrom(1024)

    message = data.decode()

    node, event, value = message.split("|")

    # Event classification + aggregation
    if event == "LATENCY_HIGH":
        latency_events += 1

    # Display event info
    print("Node:", node)
    print("Event:", event)
    print("Value:", value)

    # Aggregated visualization
    print("Total Latency Alerts:", latency_events)
    print("Total Failure Events:", failure_events)
    print("Total Performance Events:", performance_events)

    print("----------------------------------")

    # Packet loss tolerance (ACK reply)
    sock.sendto(b"ACK", addr)
