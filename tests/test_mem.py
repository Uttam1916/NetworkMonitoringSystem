import time

data = []

for i in range(200):

    block = bytearray(5_000_000)   # ~5 MB

    # touch memory so OS commits it
    for j in range(0, len(block), 4096):
        block[j] = 1

    data.append(block)

    print("Allocated", (i+1)*5, "MB")

    time.sleep(0.05)


print("Holding memory for 20 seconds")
time.sleep(20)

data.clear()

print("Memory released")