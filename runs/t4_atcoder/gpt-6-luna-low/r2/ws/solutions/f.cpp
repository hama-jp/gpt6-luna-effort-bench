#include <bits/stdc++.h>
using namespace std; using int64=long long;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
 int n; int64 mod;cin>>n>>mod;vector<int64>a(n),b(n);for(auto&x:a)cin>>x;for(auto&x:b)cin>>x;
 // u=r+c, v=r-c; Chebyshev distance = (|du|+|dv|)/2.
 int side=2*n-1; vector<int64>w((size_t)side*side);
 for(int r=0;r<n;r++)for(int c=0;c<n;c++)w[(r+c)*side+(r-c+n-1)]=(a[r]*b[c])%mod;
 vector<int64> rowW((size_t)side*side),rowX((size_t)side*side), colW((size_t)side*side),colX((size_t)side*side);
 // For every transformed-grid point, compute weighted absolute distance in both axes.
 vector<int64> fu((size_t)side*side),fv((size_t)side*side);
 for(int y=0;y<side;y++){int64 sw=0,sx=0;for(int x=0;x<side;x++){auto q=(size_t)y*side+x;sw+=w[q];sx+=w[q]*x;rowW[q]=sw;rowX[q]=sx;}
   int64 tw=sw,tx=sx; for(int x=0;x<side;x++){auto q=(size_t)y*side+x;int64 lw=rowW[q],lx=rowX[q];fu[q]=x*lw-lx+(tx-lx)-x*(tw-lw);}}
 for(int x=0;x<side;x++){int64 sw=0,sx=0;for(int y=0;y<side;y++){auto q=(size_t)y*side+x;sw+=w[q];sx+=w[q]*y;colW[q]=sw;colX[q]=sx;}
   int64 tw=sw,tx=sx; for(int y=0;y<side;y++){auto q=(size_t)y*side+x;int64 lw=colW[q],lx=colX[q];fv[q]=y*lw-lx+(tx-lx)-y*(tw-lw);}}
 int64 ans=0;for(int r=0;r<n;r++)for(int c=0;c<n;c++){int u=r+c,v=r-c+n-1;int64 f=(fu[(size_t)u*side+v]+fv[(size_t)u*side+v])/2;ans^=(f+(int64)r*n+c);}
 cout<<ans<<'\n';
}
