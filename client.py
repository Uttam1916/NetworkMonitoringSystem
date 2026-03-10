import socket
import time
import psutil
from ping3 import ping

SERVER_IP = "127.0.0.1"
PORT = 9000

NODE_ID = "node1"

LATENCY_THRESHOLD = 0.2
CPU_THRESHOLD = 30
MEM_THRESHOLD = 10

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

seq = 0

last_state = {
    "cpu": False,
    "memory": False,
    "latency": False
}


def send_event(event, metric, value):

    global seq
    seq += 1

    ts = int(time.time())

    msg = f"{NODE_ID}|{seq}|{ts}|{event}|{metric}|{value}"

    sock.sendto(msg.encode(), (SERVER_IP, PORT))


def heartbeat():
    send_event("HEARTBEAT", "status", "alive")


def check_latency():

    latency = ping("8.8.8.8", timeout=1)

    if latency is None:

        if not last_state["latency"]:
            send_event("PACKET_LOSS", "latency", 0)

        last_state["latency"] = True
        return

    if latency > LATENCY_THRESHOLD:

        if not last_state["latency"]:
            send_event("LATENCY_HIGH", "latency", latency)

        last_state["latency"] = True

    else:

        last_state["latency"] = False


def check_cpu():

    cpu = psutil.cpu_percent(interval=1)

    if cpu > CPU_THRESHOLD:

        if not last_state["cpu"]:
            send_event("CPU_HIGH", "cpu", cpu)

        last_state["cpu"] = True

    else:

        last_state["cpu"] = False


def check_memory():

    mem = psutil.virtual_memory().percent

    if mem > MEM_THRESHOLD:

        if not last_state["memory"]:
            send_event("MEMORY_HIGH", "memory", mem)

        last_state["memory"] = True

    else:

        last_state["memory"] = False


while True:

    heartbeat()

    check_latency()
    check_cpu()
    check_memory()

    time.sleep(3)