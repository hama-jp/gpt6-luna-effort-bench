#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    long long a, first = -1, second = -1, third = -1;
    for (int i = 0; i < n; ++i) {
        cin >> a;
        if (a >= first) {
            third = second;
            second = first;
            first = a;
        } else if (a >= second) {
            third = second;
            second = a;
        } else if (a > third) {
            third = a;
        }
        if (i >= 2) cout << third << '\n';
    }
}
