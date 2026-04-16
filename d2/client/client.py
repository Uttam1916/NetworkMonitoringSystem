import socket
import time
import psutil
from ping3 import ping
from cryptography.fernet import Fernet
import uuid
import threading

SERVER_IP = "10.42.249.149"
PORT = 9000

NODE_ID = f"node-{uuid.uuid4().hex[:6]}"

KEY = b'4N0zPj3C9j2mA2y7eFzQ4jYx6yXr0cZy4Yp9sL9Q6V0='
cipher = Fernet(KEY)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

seq = 0

COOLDOWN = 10
last_sent = {}

# for RTT tracking
send_times = {}


def should_send(event):
    now = time.time()
    if event not in last_sent or now - last_sent[event] > COOLDOWN:
        last_sent[event] = now
        return True
    return False


def send_event(event, metric, value):
    global seq
    seq += 1

    ts = int(time.time())
    msg = f"{NODE_ID}|{seq}|{ts}|{event}|{metric}|{value}"

    encrypted = cipher.encrypt(msg.encode())

    # store send time for RTT
    send_times[(NODE_ID, seq)] = time.time()

    sock.sendto(encrypted, (SERVER_IP, PORT))

    print(f"[SEND] {event} ({metric}={value})")


# ---- ACK RECEIVER ----

def receive_ack():
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            msg = data.decode()

            if msg.startswith("ACK"):
                _, node, seq_str = msg.split("|")
                seq_num = int(seq_str)

                key = (node, seq_num)
                if key in send_times:
                    rtt = time.time() - send_times.pop(key)
                    print(f"[RTT] {rtt*1000:.2f} ms")

        except:
            pass


# ---- METRICS ----

def heartbeat():
    send_event("HEARTBEAT", "status", "alive")


def check_cpu():
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 80 and should_send("CPU_THRESHOLD_EXCEEDED"):
        send_event("CPU_THRESHOLD_EXCEEDED", "cpu", cpu)


def check_memory():
    mem = psutil.virtual_memory().percent
    if mem > 80 and should_send("MEMORY_THRESHOLD_EXCEEDED"):
        send_event("MEMORY_THRESHOLD_EXCEEDED", "memory", mem)


def check_latency():
    try:
        latency = ping("8.8.8.8", timeout=1)
    except:
        return

    if latency is None:
        send_event("NETWORK_FAILURE", "latency", 0)
    elif latency > 0.1 and should_send("LATENCY_HIGH"):
        send_event("LATENCY_HIGH", "latency", round(latency, 4))


# ---- START ----

print(f"Client started: {NODE_ID}")

threading.Thread(target=receive_ack, daemon=True).start()

try:
    while True:
        heartbeat()
        check_cpu()
        check_memory()
        check_latency()
        time.sleep(3)

except Exception as e:
    print("ERROR:", e)
    input("Press Enter to exit...")