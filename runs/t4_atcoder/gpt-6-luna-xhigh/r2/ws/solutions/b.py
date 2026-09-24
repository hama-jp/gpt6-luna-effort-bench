import sys

data = sys.stdin.read().split()
n = int(data[0])
s, t = data[1], data[2]
print("Yes" if all(y == "*" or x == y for x, y in zip(s, t)) else "No")
