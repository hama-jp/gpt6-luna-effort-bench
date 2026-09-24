import sys
s = sys.stdin.readline().strip()
print(s + ("r" if s.endswith("e") else "er"))
