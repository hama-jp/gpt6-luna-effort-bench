import sys
z=sys.stdin.read().split(); s,t=z[1:3]
print('Yes' if all(y=='*' or x==y for x,y in zip(s,t)) else 'No')
