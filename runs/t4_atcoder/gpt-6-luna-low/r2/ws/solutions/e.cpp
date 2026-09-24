#include <bits/stdc++.h>
using namespace std;
struct Node{int mn,mx,mi,ma;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
 int n,m;cin>>n>>m; vector<int>a(n);for(int&x:a)cin>>x;
 int z=1;while(z<n)z*=2; vector<Node> t(2*z,{INT_MAX,INT_MIN,-1,-1});
 for(int i=0;i<n;i++)t[z+i]={a[i],a[i],i,i};
 auto merge=[](Node x,Node y){return Node{min(x.mn,y.mn),max(x.mx,y.mx),x.mn<=y.mn?x.mi:y.mi,x.mx>=y.mx?x.ma:y.ma};};
 for(int i=z-1;i;i--)t[i]=merge(t[2*i],t[2*i+1]);
 auto query=[&](int l,int r){Node x{INT_MAX,INT_MIN,-1,-1},y=x;for(l+=z,r+=z;l<r;l/=2,r/=2){if(l&1)x=merge(x,t[l++]);if(r&1)y=merge(t[--r],y);}return merge(x,y);};
 while(m--){int l,r;cin>>l>>r;--l;auto v=query(l,r);swap(a[v.mi],a[v.ma]);
   for(int p=z+v.mi;p;p/=2){if(p>=z)t[p]={a[p-z],a[p-z],p-z,p-z};else t[p]=merge(t[2*p],t[2*p+1]);}
   for(int p=z+v.ma;p;p/=2){if(p>=z)t[p]={a[p-z],a[p-z],p-z,p-z};else t[p]=merge(t[2*p],t[2*p+1]);}
 }
 for(int i=0;i<n;i++)cout<<a[i]<<(i+1==n?'\n':' ');
}
