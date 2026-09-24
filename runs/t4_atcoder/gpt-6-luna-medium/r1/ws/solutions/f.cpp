#include <bits/stdc++.h>
using namespace std;using ll=long long;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;ll mod;cin>>n>>mod;vector<ll>a(n),b(n);for(auto&x:a)cin>>x;for(auto&x:b)cin>>x;
 int off=2*n+2, sz=4*n+5;vector<ll>su(sz),sv(sz);
 for(int i=0;i<n;i++)for(int j=0;j<n;j++){ll w=a[i]*b[j]%mod;int u=i+j+2, v=i-j+off;su[u]+=w;sv[v]+=w;}
 vector<ll>pu(sz+1),pui(sz+1),pv(sz+1),pvi(sz+1);for(int x=0;x<sz;x++){pu[x+1]=pu[x]+su[x];pui[x+1]=pui[x]+su[x]*x;pv[x+1]=pv[x]+sv[x];pvi[x+1]=pvi[x]+sv[x]*x;}
 auto absSum=[&](int x,vector<ll>&p,vector<ll>&pi)->ll{ll l=p[x+1],li=pi[x+1],tot=p[sz],ti=pi[sz];return (ll)x*l-li+(ti-li)-(ll)x*(tot-l);};ll ans=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++){ll f=(absSum(i+j+2,pu,pui)+absSum(i-j+off,pv,pvi))/2;ll val=f+(ll)i*n+j;ans^=val;}cout<<ans<<'\n';}
