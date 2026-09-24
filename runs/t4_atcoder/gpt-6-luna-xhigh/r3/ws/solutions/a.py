import sys

s = sys.stdin.readline().strip()
print(s + ("r" if s[-1] == "e" else "er"))
