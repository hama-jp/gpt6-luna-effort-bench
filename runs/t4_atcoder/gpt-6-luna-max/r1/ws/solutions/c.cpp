#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long first = LLONG_MIN, second = LLONG_MIN, third = LLONG_MIN;
    for (int i = 0; i < n; ++i) {
        long long x;
        cin >> x;
        if (x >= first) {
            third = second;
            second = first;
            first = x;
        } else if (x >= second) {
            third = second;
            second = x;
        } else if (x > third) {
            third = x;
        }
        if (i >= 2) cout << third << '\n';
    }
}
