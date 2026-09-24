#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s, t;
    cin >> n >> s >> t;
    for (int i = 0; i < n; ++i) {
        if (t[i] != '*' && t[i] != s[i]) {
            cout << "No\n";
            return 0;
        }
    }
    cout << "Yes\n";
}
