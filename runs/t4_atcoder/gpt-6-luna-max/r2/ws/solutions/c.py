import sys
data = list(map(int, sys.stdin.buffer.read().split()))
n = data[0]
top = [-1, -1, -1]
out = []
for k, x in enumerate(data[1:]):
    if x > top[0]:
        top[0], top[1], top[2] = x, top[0], top[1]
    elif x > top[1]:
        top[1], top[2] = x, top[1]
    elif x > top[2]:
        top[2] = x
    if k >= 2:
        out.append(str(top[2]))
sys.stdout.write("\n".join(out) + "\n")
