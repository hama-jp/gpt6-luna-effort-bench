#include <bits/stdc++.h>
using namespace std;

using int64 = long long;

static vector<int64> make_prefix(const vector<int64> &weight) {
    vector<int64> pref(weight.size() + 1, 0);
    for (size_t i = 0; i < weight.size(); ++i) pref[i + 1] = pref[i] + weight[i];
    return pref;
}

static vector<int64> make_weighted_prefix(const vector<int64> &weight) {
    vector<int64> pref(weight.size() + 1, 0);
    for (size_t i = 0; i < weight.size(); ++i) {
        pref[i + 1] = pref[i] + (int64)i * weight[i];
    }
    return pref;
}

static int64 abs_sum(int x, const vector<int64> &pref_w, const vector<int64> &pref_xw) {
    int64 left_w = pref_w[x + 1];
    int64 left_xw = pref_xw[x + 1];
    int64 total_w = pref_w.back();
    int64 total_xw = pref_xw.back();
    int64 right_w = total_w - left_w;
    int64 right_xw = total_xw - left_xw;
    return (int64)x * left_w - left_xw + right_xw - (int64)x * right_w;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    int64 mod;
    cin >> n >> mod;
    vector<int64> a(n), b(n);
    for (auto &v : a) cin >> v;
    for (auto &v : b) cin >> v;

    vector<int64> diag_sum(2 * n - 1, 0), anti_sum(2 * n - 1, 0);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int64 w = (a[i] * b[j]) % mod;
            diag_sum[i + j] += w;
            anti_sum[i - j + n - 1] += w;
        }
    }

    auto diag_w = make_prefix(diag_sum);
    auto diag_xw = make_weighted_prefix(diag_sum);
    auto anti_w = make_prefix(anti_sum);
    auto anti_xw = make_weighted_prefix(anti_sum);

    int64 answer = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int64 su = abs_sum(i + j, diag_w, diag_xw);
            int64 sv = abs_sum(i - j + n - 1, anti_w, anti_xw);
            int64 f = (su + sv) / 2;
            answer ^= f + (int64)i * n + j;
        }
    }
    cout << answer << '\n';
    return 0;
}
