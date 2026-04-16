import socket
import time
import uuid
from collections import deque

import psutil
from cryptography.fernet import Fernet

# ---- CONFIG ----
SERVER_IP = "192.168.137.1"
PORT = 9000
KEY = b'4N0zPj3C9j2mA2y7eFzQ4jYx6yXr0cZy4Yp9sL9Q6V0='

INTERVAL = 3
COOLDOWN = 10

# ---- SETUP ----
NODE_ID = f"node-{uuid.uuid4().hex[:8]}"
START_TIME = time.time()

cipher = Fernet(KEY)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)

seq = 0
last_sent = {}

# ---- TRACKING ----
send_times = {}
sent = 0
dropped = 0

latency_hist = deque(maxlen=10)

# ---- HELPERS ----
def next_seq():
    global seq
    seq += 1
    return seq


def should_alert(event):
    now = time.time()
    if event not in last_sent or now - last_sent[event] > COOLDOWN:
        last_sent[event] = now
        return True
    return False


# ---- SEND ----
def send_event(event, metric, value):
    global sent, dropped

    s = next_seq()
    ts = int(time.time())

    msg = f"{NODE_ID}|{s}|{ts}|{event}|{metric}|{value}"
    encrypted = cipher.encrypt(msg.encode())

    send_times[s] = time.time()
    sent += 1

    try:
        sock.sendto(encrypted, (SERVER_IP, PORT))

        data, _ = sock.recvfrom(1024)
        ack = data.decode().split("|")

        if ack[0] == "ACK" and int(ack[2]) == s:
            rtt = (time.time() - send_times.pop(s)) * 1000
            print(f"[ACK] {event:<25} RTT={rtt:.1f}ms")

            # send RTT to server
            send_event("RTT", "rtt_ms", round(rtt, 2))
            print(f"[RTT SENT] {rtt:.2f} ms")
            return

    except:
        dropped += 1
        print(f"[DROP] {event}")


# ---- METRICS ----

def heartbeat():
    uptime = int(time.time() - START_TIME)
    send_event("HEARTBEAT", "uptime_s", uptime)


def cpu():
    val = psutil.cpu_percent(interval=0.3)
    send_event("CPU_USAGE", "cpu_pct", val)

    if val > 80 and should_alert("CPU_THRESHOLD_EXCEEDED"):
        send_event("CPU_THRESHOLD_EXCEEDED", "cpu_pct", val)


def memory():
    val = psutil.virtual_memory().percent
    send_event("MEMORY_USAGE", "mem_pct", val)

    if val > 80 and should_alert("MEMORY_THRESHOLD_EXCEEDED"):
        send_event("MEMORY_THRESHOLD_EXCEEDED", "mem_pct", val)


def disk():
    try:
        path = "C:\\" if psutil.WINDOWS else "/"
        val = psutil.disk_usage(path).percent
        send_event("DISK_USAGE", "disk_pct", val)

        if val > 90 and should_alert("DISK_USAGE_HIGH"):
            send_event("DISK_USAGE_HIGH", "disk_pct", val)
    except:
        pass


def latency():
    try:
        start = time.time()
        socket.create_connection(("8.8.8.8", 53), timeout=2).close()
        l = (time.time() - start) * 1000
    except:
        if should_alert("NETWORK_FAILURE"):
            send_event("NETWORK_FAILURE", "latency_ms", 0)
        return

    latency_hist.append(l)

    send_event("NETWORK_LATENCY", "latency_ms", round(l, 2))

    if len(latency_hist) > 1:
        jitter = max(latency_hist) - min(latency_hist)
        send_event("NETWORK_JITTER", "jitter_ms", round(jitter, 2))

    if l > 100 and should_alert("LATENCY_HIGH"):
        send_event("LATENCY_HIGH", "latency_ms", l)


def bandwidth():
    now = time.time()
    curr = psutil.net_io_counters()

    if not hasattr(bandwidth, "last"):
        bandwidth.last = curr
        bandwidth.last_time = now
        return

    delta = (curr.bytes_sent - bandwidth.last.bytes_sent +
             curr.bytes_recv - bandwidth.last.bytes_recv)

    rate = delta / (now - bandwidth.last_time)

    bandwidth.last = curr
    bandwidth.last_time = now

    send_event("BANDWIDTH_USAGE", "bps", int(rate))

    if rate > 10_000_000 and should_alert("BANDWIDTH_SPIKE"):
        send_event("BANDWIDTH_SPIKE", "bps", int(rate))


def connections():
    try:
        c = len([x for x in psutil.net_connections() if x.status == "ESTABLISHED"])
        send_event("TCP_CONNECTIONS", "count", c)
    except:
        pass


def packet_loss():
    if sent == 0:
        return

    loss = (dropped / sent) * 100
    send_event("PACKET_LOSS", "loss_pct", round(loss, 2))


# ---- MAIN LOOP ----
print("Client started:", NODE_ID)

while True:
    try:
        heartbeat()
        cpu()
        memory()
        disk()
        latency()
        bandwidth()
        connections()
        packet_loss()

    except Exception as e:
        print("[ERROR]", e)

    time.sleep(INTERVAL)