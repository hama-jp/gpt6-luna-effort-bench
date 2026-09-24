import sys
it=iter(map(int,sys.stdin.buffer.read().split()))
n=next(it); a=[next(it) for _ in range(n)]
top=[0,0,0]
out=[]
for x in a:
    if x>top[0]: top=[x,top[0],top[1]]
    elif x>top[1]: top=[top[0],x,top[1]]
    elif x>top[2]: top[2]=x
    if top[2]: out.append(str(top[2]))
sys.stdout.write('\n'.join(out))
