import socket
import time
import psutil
from ping3 import ping

SERVER_IP = "YOUR_SERVER_IP"
PORT = 9000
NODE_ID = "node1"

LATENCY_THRESHOLD = 0.2
CPU_THRESHOLD = 80
MEM_THRESHOLD = 80

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sequence = 0


def send_event(event, metric, value):

    global sequence
    sequence += 1

    ts = int(time.time())

    message = f"{NODE_ID}|{sequence}|{ts}|{event}|{metric}|{value}"

    sock.sendto(message.encode(), (SERVER_IP, PORT))

    print("Sent:", message)


def check_latency():

    latency = ping("8.8.8.8", timeout=1)

    if latency is None:
        send_event("PACKET_LOSS", "latency", 0)

    elif latency > LATENCY_THRESHOLD:
        send_event("LATENCY_HIGH", "latency", latency)


def check_cpu():

    cpu = psutil.cpu_percent()

    if cpu > CPU_THRESHOLD:
        send_event("CPU_HIGH", "cpu", cpu)


def check_memory():

    mem = psutil.virtual_memory().percent

    if mem > MEM_THRESHOLD:
        send_event("MEMORY_HIGH", "memory", mem)


while True:

    check_latency()
    check_cpu()
    check_memory()

    time.sleep(5)