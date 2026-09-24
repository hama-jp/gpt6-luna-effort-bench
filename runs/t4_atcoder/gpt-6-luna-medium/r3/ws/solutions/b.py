n=int(input()); s=input().strip(); t=input().strip()
print('Yes' if all(y=='*' or x==y for x,y in zip(s,t)) else 'No')
