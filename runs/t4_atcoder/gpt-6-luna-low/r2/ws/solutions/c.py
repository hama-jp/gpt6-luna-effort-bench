import sys
data = list(map(int, sys.stdin.buffer.read().split()))
n = data[0]; a = data[1:]
top = [0, 0, 0]
out = []
for idx, x in enumerate(a):
    if x >= top[0]: top = [x, top[0], top[1]]
    elif x >= top[1]: top = [top[0], x, top[1]]
    elif x > top[2]: top[2] = x
    if idx >= 2:
        out.append(str(top[2]))
print('\n'.join(out))
