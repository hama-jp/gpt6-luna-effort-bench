import sys
it=iter(map(int,sys.stdin.buffer.read().split())); n=next(it)
a=[next(it) for _ in range(n)]
x=y=z=0; out=[]
for i,v in enumerate(a):
    if v>=x: z,y,x=y,x,v
    elif v>=y: z,y=y,v
    elif v>z: z=v
    if i>=2: out.append(str(z))
sys.stdout.write('\n'.join(out))
