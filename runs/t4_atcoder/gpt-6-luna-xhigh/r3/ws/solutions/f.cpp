#include <bits/stdc++.h>
using namespace std;
using int64 = long long;

struct Prefix {
    vector<int64> w, iw;
    void build(const vector<int64> &a) {
        int n = a.size();
        w.assign(n + 1, 0);
        iw.assign(n + 1, 0);
        for (int i = 0; i < n; ++i) {
            w[i + 1] = w[i] + a[i];
            iw[i + 1] = iw[i] + a[i] * i;
        }
    }
    int64 abs_sum(int x) const {
        int n = (int)w.size() - 1;
        int64 left_w = w[x], left_iw = iw[x];
        int64 through_w = w[x + 1], through_iw = iw[x + 1];
        int64 right_w = w[n] - through_w;
        int64 right_iw = iw[n] - through_iw;
        return (int64)x * left_w - left_iw + right_iw - (int64)x * right_w;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    int64 mod;
    cin >> n >> mod;
    vector<int64> a(n), b(n);
    for (auto &v : a) cin >> v;
    for (auto &v : b) cin >> v;

    vector<int64> hu(2 * n - 1), hv(2 * n - 1);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int64 w = (a[i] * b[j]) % mod;
            hu[i + j] += w;
            hv[i - j + n - 1] += w;
        }
    }
    Prefix pu, pv;
    pu.build(hu);
    pv.build(hv);

    int64 ans = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int u = i + j;
            int v = i - j + n - 1;
            int64 f = (pu.abs_sum(u) + pv.abs_sum(v)) / 2;
            ans ^= f + (int64)i * n + j;
        }
    }
    cout << ans << '\n';
}
