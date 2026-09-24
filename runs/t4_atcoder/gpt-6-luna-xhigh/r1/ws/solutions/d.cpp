#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    long long k, x, y;
    cin >> n >> m >> k >> x >> y;
    vector<long long> a(n), drinks(m);
    for (auto &v : a) cin >> v;
    for (auto &v : drinks) {
        long long price;
        cin >> price;
        v = (price + k - 1) / k;
    }
    sort(a.begin(), a.end());
    sort(drinks.begin(), drinks.end());
    vector<long long> pa(n + 1), pd(m + 1);
    for (int i = 0; i < n; ++i) pa[i + 1] = pa[i] + a[i];
    for (int i = 0; i < m; ++i) pd[i + 1] = pd[i] + drinks[i];
    long long ans = 0;
    for (int cnt = 0; cnt <= m; ++cnt) {
        if (pd[cnt] > y) break;
        long long budget = x + k * (y - pd[cnt]);
        int desserts = upper_bound(pa.begin(), pa.end(), budget) - pa.begin() - 1;
        ans = max(ans, (long long)cnt + desserts);
    }
    cout << ans << '\n';
}
