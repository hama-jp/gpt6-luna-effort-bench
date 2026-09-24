import sys
it=sys.stdin.read().split()
n=int(it[0]); s,t=it[1:3]
print('Yes' if all(y=='*' or x==y for x,y in zip(s,t)) else 'No')
