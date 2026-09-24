#include <bits/stdc++.h>
using namespace std; using int64=long long;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n; long long mod;cin>>n>>mod;vector<long long>a(n),b(n);for(auto&x:a)cin>>x;for(auto&x:b)cin>>x;
// Chebyshev distance max(dx,dy) = (|dx+dy|+|dx-dy|)/2. Transform coordinates u=r+c,v=r-c.
// weighted absolute-distance sums are separable after aggregation over opposite coordinate.
vector<long long> u(2*n-1),v(2*n-1); // count-weighted population per transformed coordinate
// direct aggregate O(N^2) impossible; population is product-mod, calculate row/col slices per cell O(N^2) still 2.25m okay.
vector<vector<long long>> w(n,vector<long long>(n));
for(int i=0;i<n;i++)for(int j=0;j<n;j++)w[i][j]=a[i]*b[j]%mod;
// For each target, separable absolute distance via row/column prefix: calculate sums over all people for each target using O(N^2) prefix per row/col? max identity requires u/v distributions.
vector<long long> su(2*n+1),sv(2*n+1);for(int i=0;i<n;i++)for(int j=0;j<n;j++){long long z=w[i][j];su[i+j]+=z;sv[i-j+n-1]+=z;}
auto makeAbs=[](const vector<long long>& c){int z=c.size();vector<long long> p(z+1),q(z+1),out(z);for(int i=0;i<z;i++){p[i+1]=p[i]+c[i];q[i+1]=q[i]+c[i]*i;}for(int x=0;x<z;x++)out[x]=(long long)x*p[x]-q[x]+(q[z]-q[x])-(long long)x*(p[z]-p[x]);return out;};auto fu=makeAbs(su),fv=makeAbs(sv);
long long ans=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++){long long f=(fu[i+j]+fv[i-j+n-1])/2; long long q=f+(long long)i*n+j;ans^=q;}cout<<ans<<'\n';}
