import threading
import time


def burn():

    end = time.time() + 20

    while time.time() < end:
        x = 0
        for i in range(1000000):
            x += i


threads = []

for _ in range(6):

    t = threading.Thread(target=burn)
    t.start()
    threads.append(t)


for t in threads:
    t.join()