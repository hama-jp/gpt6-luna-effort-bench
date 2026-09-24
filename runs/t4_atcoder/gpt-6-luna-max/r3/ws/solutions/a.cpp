#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    cin >> s;
    cout << s << (s.back() == 'e' ? "r" : "er") << '\n';
    return 0;
}
