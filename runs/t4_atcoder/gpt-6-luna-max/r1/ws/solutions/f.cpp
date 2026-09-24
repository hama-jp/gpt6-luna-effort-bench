#include <bits/stdc++.h>
using namespace std;

static vector<long long> abs_distance_sums(const vector<long long>& mass,
                                           const vector<long long>& weighted_coord) {
    int n = (int)mass.size();
    vector<long long> pref_mass(n + 1), pref_weighted(n + 1);
    for (int i = 0; i < n; ++i) {
        pref_mass[i + 1] = pref_mass[i] + mass[i];
        pref_weighted[i + 1] = pref_weighted[i] + weighted_coord[i];
    }
    vector<long long> result(n);
    long long total_mass = pref_mass[n], total_weighted = pref_weighted[n];
    for (int x = 0; x < n; ++x) {
        long long left_mass = pref_mass[x + 1];
        long long left_weighted = pref_weighted[x + 1];
        long long right_mass = total_mass - left_mass;
        long long right_weighted = total_weighted - left_weighted;
        result[x] = x * left_mass - left_weighted + right_weighted - x * right_mass;
    }
    return result;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long mod;
    cin >> n >> mod;
    vector<long long> a(n), b(n);
    for (auto &x : a) cin >> x;
    for (auto &x : b) cin >> x;

    int len = 2 * n - 1;
    vector<long long> mass_u(len), weighted_u(len), mass_v(len), weighted_v(len);
    for (int r = 0; r < n; ++r) {
        for (int c = 0; c < n; ++c) {
            long long people = (a[r] * b[c]) % mod;
            int u = r + c;
            int v = r - c + n - 1;
            mass_u[u] += people;
            weighted_u[u] += people * u;
            mass_v[v] += people;
            weighted_v[v] += people * v;
        }
    }

    vector<long long> dist_u = abs_distance_sums(mass_u, weighted_u);
    vector<long long> dist_v = abs_distance_sums(mass_v, weighted_v);

    long long answer = 0;
    for (int r = 0; r < n; ++r) {
        for (int c = 0; c < n; ++c) {
            int u = r + c;
            int v = r - c + n - 1;
            long long fare_sum = (dist_u[u] + dist_v[v]) / 2;
            long long index = 1LL * r * n + c;
            answer ^= (fare_sum + index);
        }
    }
    cout << answer << '\n';
}
