import sys
it = iter(sys.stdin.buffer.read().split())
n = int(next(it))
s = next(it)
t = next(it)
print("Yes" if all(y == 42 or x == y for x, y in zip(s, t)) else "No")
