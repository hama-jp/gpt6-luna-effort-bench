#include <bits/stdc++.h>
using namespace std;

long long abs_weighted_sum(const vector<long long> &pw,
                           const vector<long long> &px,
                           int pos) {
    int n = (int)pw.size() - 1;
    long long total_w = pw[n], total_x = px[n];
    long long left_w = pw[pos + 1], left_x = px[pos + 1];
    long long right_w = total_w - left_w, right_x = total_x - left_x;
    return 1LL * pos * left_w - left_x + right_x - 1LL * pos * right_w;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long mod;
    cin >> n >> mod;
    vector<long long> a(n), b(n);
    for (auto &v : a) cin >> v;
    for (auto &v : b) cin >> v;

    int dsz = 2 * n - 1;
    vector<long long> sum_u(dsz, 0), sum_v(dsz, 0);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            long long w = (a[i] * b[j]) % mod;
            sum_u[i + j] += w;
            sum_v[i - j + n - 1] += w;
        }
    }

    vector<long long> pu(dsz + 1, 0), pux(dsz + 1, 0);
    vector<long long> pv(dsz + 1, 0), pvx(dsz + 1, 0);
    for (int x = 0; x < dsz; ++x) {
        pu[x + 1] = pu[x] + sum_u[x];
        pux[x + 1] = pux[x] + sum_u[x] * x;
        pv[x + 1] = pv[x] + sum_v[x];
        pvx[x + 1] = pvx[x] + sum_v[x] * x;
    }

    long long answer = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            long long du = abs_weighted_sum(pu, pux, i + j);
            long long dv = abs_weighted_sum(pv, pvx, i - j + n - 1);
            long long f = (du + dv) / 2;
            answer ^= f + 1LL * i * n + j;
        }
    }
    cout << answer << '\n';
}
