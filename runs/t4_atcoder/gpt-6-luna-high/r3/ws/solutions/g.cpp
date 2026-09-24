#include <bits/stdc++.h>
using namespace std;
const int D=61; const long long NEG=-(1LL<<60);
using Mat=array<array<long long,D>,D>;
Mat ident(){Mat a;for(int i=0;i<D;i++)for(int j=0;j<D;j++)a[i][j]=(i==j?0:NEG);return a;}
Mat mul(const Mat&a,const Mat&b){Mat c;for(int i=0;i<D;i++){c[i].fill(NEG);for(int k=0;k<D;k++)if(a[i][k]>NEG/2)for(int j=0;j<D;j++)if(b[k][j]>NEG/2)c[i][j]=max(c[i][j],a[i][k]+b[k][j]);}return c;}
Mat shifted(const Mat&a,int by,int active){Mat z=ident();for(int i=0;i<=active;i++){int r=i+by;for(int j=0;j<D;j++){int col;if(j<by)continue;else if(j<=active+by)col=j-by;else col=active;z[r][j]=a[i][col];}}return z;}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);vector<Mat>T(61);T[0]=ident();for(int j=0;j<D;j++)T[0][0][j]=j==0?1:NEG;for(int b=1;b<D;b++){Mat s=shifted(T[b-1],1,b-1);T[b]=mul(s,T[b-1]);}
 int tc;cin>>tc;while(tc--){unsigned long long L,R;cin>>L>>R;vector<long long>dp(D,0);unsigned long long cur=L;while(cur<=R){int b=0;if(cur==0)b=60;else b=__builtin_ctzll(cur);unsigned long long rem=R-cur+1;while((1ULL<<b)>rem)b--;int off=__builtin_popcountll(cur>>b);int high=off+b;vector<long long>ndp=dp;for(int i=0;i<=b;i++){int row=i+off;long long best=NEG;for(int j=0;j<=b;j++)if(T[b][i][j]>NEG/2)best=max(best,dp[j+off]+T[b][i][j]);long long highdp=NEG;for(int j=high+1;j<D;j++)highdp=max(highdp,dp[j]);if(highdp>NEG/2)best=max(best,highdp+T[b][i][b]);ndp[row]=best;}dp.swap(ndp);if(R-cur+1==(1ULL<<b))break;cur+=(1ULL<<b);}cout<<*max_element(dp.begin(),dp.end())<<'\n';}}
