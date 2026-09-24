import sys,bisect
it=iter(map(int,sys.stdin.buffer.read().split()))
n=next(it);m=next(it);k=next(it);x=next(it);y=next(it)
a=sorted(next(it) for _ in range(n)); b=sorted((next(it)+k-1)//k for _ in range(m))
pref=[0]
for v in b: pref.append(pref[-1]+v)
s=0;ans=0
for d in range(n+1):
    if d: s+=a[d-1]
    notes=max(0,(s-x+k-1)//k)
    if notes<=y:
        ans=max(ans,d+bisect.bisect_right(pref,y-notes)-1)
print(ans)
