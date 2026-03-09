from ping3 import ping
import socket
import time

SERVER_IP = "127.0.0.1"
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    latency = ping("8.8.8.8")

    if latency and latency > 0.2:
        message = f"node1|LATENCY_HIGH|{latency}"

        sock.sendto(message.encode(), (SERVER_IP, PORT))
        print("Event sent:", message)

    time.sleep(5)