#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    string s, t;
    cin >> n >> s >> t;
    bool ok = true;
    for (int i = 0; i < n; ++i) if (t[i] != '*' && t[i] != s[i]) ok = false;
    cout << (ok ? "Yes" : "No") << '\n';
}
