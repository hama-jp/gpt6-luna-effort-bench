#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long top[3] = {-1, -1, -1};
    for (int i = 0; i < n; ++i) {
        long long x;
        cin >> x;
        for (int j = 0; j < 3; ++j) {
            if (x > top[j]) {
                for (int k = 2; k > j; --k) top[k] = top[k - 1];
                top[j] = x;
                break;
            }
        }
        if (i >= 2) cout << top[2] << '\n';
    }
    return 0;
}
