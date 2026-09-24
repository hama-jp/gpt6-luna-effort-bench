#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    long long k;
    cin >> n >> m >> k;
    long long x, y;
    cin >> x >> y;

    vector<long long> a(n), b(m);
    for (auto &v : a) cin >> v;
    for (auto &v : b) cin >> v;
    sort(a.begin(), a.end());
    sort(b.begin(), b.end());

    vector<long long> pa(n + 1, 0), pb(m + 1, 0), bills(m + 1, 0);
    for (int i = 0; i < n; ++i) pa[i + 1] = pa[i] + a[i];
    for (int i = 0; i < m; ++i) {
        pb[i + 1] = pb[i] + b[i];
        bills[i + 1] = bills[i] + (b[i] + k - 1) / k;
    }

    const long long budget = x + k * y;
    int answer = 0;
    for (int drinks = 0; drinks <= m && bills[drinks] <= y; ++drinks) {
        long long remaining = budget - pb[drinks];
        if (remaining < 0) continue;
        int desserts = upper_bound(pa.begin(), pa.end(), remaining) - pa.begin() - 1;
        answer = max(answer, drinks + desserts);
    }

    cout << answer << '\n';
    return 0;
}
