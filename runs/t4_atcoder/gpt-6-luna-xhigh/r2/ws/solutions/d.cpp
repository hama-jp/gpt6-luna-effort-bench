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

    vector<long long> desserts(n), drinks(m);
    for (auto &a : desserts) cin >> a;
    for (auto &b : drinks) cin >> b;
    sort(desserts.begin(), desserts.end());
    sort(drinks.begin(), drinks.end());

    vector<long long> dessert_prefix(n + 1, 0);
    for (int i = 0; i < n; ++i) dessert_prefix[i + 1] = dessert_prefix[i] + desserts[i];

    vector<long long> drink_price_prefix(m + 1, 0), drink_note_prefix(m + 1, 0);
    for (int i = 0; i < m; ++i) {
        drink_price_prefix[i + 1] = drink_price_prefix[i] + drinks[i];
        drink_note_prefix[i + 1] = drink_note_prefix[i] + (drinks[i] + k - 1) / k;
    }

    const long long total_money = x + y * k;
    int answer = 0;
    for (int d = 0; d <= m; ++d) {
        if (drink_note_prefix[d] > y) break;
        long long remaining = total_money - drink_price_prefix[d];
        if (remaining < 0) continue;
        int e = upper_bound(dessert_prefix.begin(), dessert_prefix.end(), remaining) - dessert_prefix.begin() - 1;
        answer = max(answer, d + e);
    }

    cout << answer << '\n';
}
