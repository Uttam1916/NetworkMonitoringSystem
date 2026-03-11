from ping3 import ping
import socket
import time

SERVER_IP = "127.0.0.1"
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    
    latency = ping("8.8.8.8")

    # Event detection + edge filtering
    if latency and latency > 0.2:

        message = f"node1|LATENCY_HIGH|{latency}"

        # Send event
        sock.sendto(message.encode(), (SERVER_IP, PORT))

        print("Event sent:", message)

        # Packet loss tolerance (ACK system)
        sock.settimeout(2)

        try:
            ack, _ = sock.recvfrom(1024)
            print("ACK received from server")

        except socket.timeout:
            print("ACK not received. Resending event...")
            sock.sendto(message.encode(), (SERVER_IP, PORT))

    time.sleep(5)
