import sys
from math import comb

def hist(x):
    if x<0:return [0]*61
    h=[0]*61; ones=0
    for bit in range(60,-1,-1):
        if (x>>bit)&1:
            for k in range(61):
                q=k-ones
                if 0<=q<=bit:h[k]+=comb(bit,q)
            ones+=1
    h[ones]+=1
    return h
z=list(map(int,sys.stdin.buffer.read().split())); t=z[0];out=[]
for i in range(t):
 l,r=z[1+2*i:3+2*i]; a=hist(r);b=hist(l-1);out.append(str(max(x-y for x,y in zip(a,b))))
print('\n'.join(out))
