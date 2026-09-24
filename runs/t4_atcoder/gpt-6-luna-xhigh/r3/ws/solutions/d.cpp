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

    vector<long long> dessert(n + 1, 0);
    for (int i = 0; i < n; ++i) dessert[i + 1] = dessert[i] + a[i];

    const long long budget = x + k * y;
    long long answer = 0, drink_cost = 0, bills = 0;
    for (int cnt = 0; cnt <= m; ++cnt) {
        if (bills <= y && drink_cost <= budget) {
            int dc = upper_bound(dessert.begin(), dessert.end(), budget - drink_cost) - dessert.begin() - 1;
            answer = max(answer, (long long)cnt + dc);
        }
        if (cnt == m) break;
        drink_cost += b[cnt];
        bills += (b[cnt] + k - 1) / k;
    }
    cout << answer << '\n';
}
