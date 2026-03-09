import socket

HOST = "0.0.0.0"
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("Monitoring server started on port", PORT)

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode()
    node, event, value = message.split("|")

    print("Node:", node)
    print("Event:", event)
    print("Value:", value)
    print("Message:", message)
    print()