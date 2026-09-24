#include <bits/stdc++.h>
using namespace std;
int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n,m; long long k,x,y;
    cin >> n >> m >> k >> x >> y;
    vector<long long>a(n),b(m);
    for(auto&v:a)cin>>v; for(auto&v:b)cin>>v;
    sort(a.begin(),a.end()); sort(b.begin(),b.end());
    vector<long long> pa(n+1),pb(m+1),pq(m+1);
    for(int i=0;i<n;i++)pa[i+1]=pa[i]+a[i];
    for(int i=0;i<m;i++){pb[i+1]=pb[i]+b[i];pq[i+1]=pq[i]+(b[i]+k-1)/k;}
    long long cash=x+y*k, ans=0;
    for(int d=0;d<=m && pq[d]<=y && pb[d]<=cash;d++){
        int z=upper_bound(pa.begin(),pa.end(),cash-pb[d])-pa.begin()-1;
        ans=max(ans,(long long)d+z);
    }
    cout<<ans<<'\n';
}
