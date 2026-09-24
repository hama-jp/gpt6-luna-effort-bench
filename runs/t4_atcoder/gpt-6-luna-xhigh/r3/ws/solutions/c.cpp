#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long top1 = -1, top2 = -1, top3 = -1;
    for (int i = 0; i < n; ++i) {
        long long x;
        cin >> x;
        if (x >= top1) {
            top3 = top2;
            top2 = top1;
            top1 = x;
        } else if (x >= top2) {
            top3 = top2;
            top2 = x;
        } else if (x > top3) {
            top3 = x;
        }
        if (i >= 2) cout << top3 << '\n';
    }
}
