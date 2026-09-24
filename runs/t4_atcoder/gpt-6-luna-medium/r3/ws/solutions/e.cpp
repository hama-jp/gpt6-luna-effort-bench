#include <bits/stdc++.h>
using namespace std;
struct Node{int mn,mx,imn,imx;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;vector<int>a(n);for(int&x:a)cin>>x;int z=1;while(z<n)z*=2;vector<Node>t(2*z);for(int i=0;i<n;i++)t[z+i]={a[i],a[i],i,i};for(int i=z-1;i;i--){auto l=t[2*i],r=t[2*i+1];t[i]={min(l.mn,r.mn),max(l.mx,r.mx),l.mn<r.mn?l.imn:r.imn,l.mx>r.mx?l.imx:r.imx};}
auto upd=[&](int p,int v){int k=z+p;a[p]=v;t[k]={v,v,p,p};for(k/=2;k;k/=2){auto l=t[2*k],r=t[2*k+1];t[k]={min(l.mn,r.mn),max(l.mx,r.mx),l.mn<r.mn?l.imn:r.imn,l.mx>r.mx?l.imx:r.imx};}};
auto query=[&](int l,int r){Node L{INT_MAX,INT_MIN,-1,-1},R=L;for(l+=z,r+=z;l<r;l/=2,r/=2){if(l&1){auto x=t[l++];if(x.mn<L.mn)L.mn=x.mn,L.imn=x.imn;if(x.mx>L.mx)L.mx=x.mx,L.imx=x.imx;}if(r&1){auto x=t[--r];if(x.mn<R.mn)R.mn=x.mn,R.imn=x.imn;if(x.mx>R.mx)R.mx=x.mx,R.imx=x.imx;}}Node o=L;if(R.mn<o.mn)o.mn=R.mn,o.imn=R.imn;if(R.mx>o.mx)o.mx=R.mx,o.imx=R.imx;return o;};
while(m--){int l,r;cin>>l>>r;--l;auto x=query(l,r);int u=a[x.imn],v=a[x.imx];upd(x.imn,v);upd(x.imx,u);}for(int i=0;i<n;i++)cout<<a[i]<<(i+1==n?'\n':' ');}
