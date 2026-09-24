#include <bits/stdc++.h>
using namespace std;
using int64 = long long;

struct PrefixAbs {
    vector<int64> cnt, sum;
    explicit PrefixAbs(int size) : cnt(size + 1, 0), sum(size + 1, 0) {}
    void add(int idx, int64 weight, int64 coordinate) {
        cnt[idx + 1] += weight;
        sum[idx + 1] += weight * coordinate;
    }
    void build() {
        for (int i = 1; i < (int)cnt.size(); ++i) {
            cnt[i] += cnt[i - 1];
            sum[i] += sum[i - 1];
        }
    }
    int64 query(int idx, int64 q) const {
        // idx is the zero-based bucket corresponding to coordinate q.
        int p = idx + 1;
        int64 left_count = cnt[p], left_sum = sum[p];
        int64 all_count = cnt.back(), all_sum = sum.back();
        return q * left_count - left_sum + (all_sum - left_sum) - q * (all_count - left_count);
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    int64 mod;
    cin >> n >> mod;
    vector<int64> a(n), b(n);
    for (auto &x : a) cin >> x;
    for (auto &x : b) cin >> x;
    PrefixAbs plus(2 * n + 1), minus(2 * n + 1);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int64 w = (a[i] * b[j]) % mod;
            int s = (i + 1) + (j + 1);
            int d = (i + 1) - (j + 1);
            plus.add(s, w, s);
            minus.add(d + n, w, d);
        }
    }
    plus.build();
    minus.build();
    int64 ans = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int rp = (i + 1) + (j + 1);
            int rm = (i + 1) - (j + 1);
            int64 g1 = plus.query(rp, rp);
            int64 g2 = minus.query(rm + n, rm);
            int64 f = (g1 + g2) / 2;
            ans ^= f + (int64)i * n + j;
        }
    }
    cout << ans << '\n';
}
