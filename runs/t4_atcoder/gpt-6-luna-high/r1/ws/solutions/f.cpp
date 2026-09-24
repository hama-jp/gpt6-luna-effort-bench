#include <bits/stdc++.h>
using namespace std;
using int64=long long;
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);
 int n; int64 mod; if(!(cin>>n>>mod))return 0;
 vector<int64>a(n),b(n);for(auto&x:a)cin>>x;for(auto&x:b)cin>>x;
 int sz=2*n+2, off=n;
 vector<int64> cu(sz),su(sz),cv(sz),sv(sz);
 for(int i=0;i<n;i++)for(int j=0;j<n;j++){
   int64 w=(a[i]*b[j])%mod;
   int u=i+j, v=i-j+off;
   cu[u]+=w; su[u]+=w*u;
   cv[v]+=w; sv[v]+=w*(v-off);
 }
 vector<int64> pcu(sz+1),psu(sz+1),pcv(sz+1),psv(sz+1);
 for(int i=0;i<sz;i++){pcu[i+1]=pcu[i]+cu[i];psu[i+1]=psu[i]+su[i];pcv[i+1]=pcv[i]+cv[i];psv[i+1]=psv[i]+sv[i];}
 auto absu=[&](int x)->int64{int q=x; int64 left=pcu[q+1], wl=psu[q+1];int64 all=pcu[sz], wa=psu[sz];return (int64)x*left-wl+(wa-wl)-(int64)x*(all-left);};
 auto absv=[&](int x)->int64{int q=x+off;int64 left=pcv[q+1],wl=psv[q+1];int64 all=pcv[sz],wa=psv[sz];return (int64)x*left-wl+(wa-wl)-(int64)x*(all-left);};
 int64 ans=0;
 for(int i=0;i<n;i++)for(int j=0;j<n;j++){
   int64 f=(absu(i+j)+absv(i-j))/2;
   ans^=(f+(int64)i*n+j);
 }
 cout<<ans<<'\n';
}
