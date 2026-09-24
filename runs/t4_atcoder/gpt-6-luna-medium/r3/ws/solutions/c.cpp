#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n;long long x; long long f=-1,s=-1,t=-1;for(int i=0;i<n;i++){cin>>x;if(x>f)t=s,s=f,f=x;else if(x>s)t=s,s=x;else if(x>t)t=x;if(i>=2)cout<<t<<'\n';}}
