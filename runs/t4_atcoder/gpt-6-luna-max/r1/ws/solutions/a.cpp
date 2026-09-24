#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    cin >> s;
    if (s.back() == 'e') s += 'r';
    else s += "er";
    cout << s << '\n';
}
