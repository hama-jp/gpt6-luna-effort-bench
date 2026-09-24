#include <bits/stdc++.h>
using namespace std;
int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n; cin >> n;
    long long a,b,c; cin >> a >> b >> c;
    multiset<long long> top{a,b,c};
    cout << *top.begin() << '\n';
    for(int i=3;i<n;i++){
        long long x; cin >> x;
        if(x>*top.begin()){ top.erase(top.begin()); top.insert(x); }
        cout << *top.begin() << '\n';
    }
}
