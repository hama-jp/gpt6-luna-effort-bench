#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n; long long a[3]; for(int i=0;i<3;i++)cin>>a[i]; sort(a,a+3,greater<long long>()); cout<<a[2]<<'\n'; for(int i=3;i<n;i++){long long x;cin>>x;if(x>a[0]){a[2]=a[1];a[1]=a[0];a[0]=x;}else if(x>a[1]){a[2]=a[1];a[1]=x;}else if(x>a[2])a[2]=x; cout<<a[2]<<'\n';}}
