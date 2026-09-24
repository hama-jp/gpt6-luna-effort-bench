import sys
it=iter(sys.stdin.read().split()); n=int(next(it)); s=next(it); t=next(it)
print('Yes' if all(y=='*' or x==y for x,y in zip(s,t)) else 'No')
