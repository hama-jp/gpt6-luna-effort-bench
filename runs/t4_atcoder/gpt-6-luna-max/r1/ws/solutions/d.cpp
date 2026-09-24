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

    long long used_k = 0;
    int eligible_drinks = 0;
    for (long long price : drinks) {
        long long need = (price + k - 1) / k;
        if (used_k + need > y) break;
        used_k += need;
        ++eligible_drinks;
    }

    long long budget = x + y * k;
    long long spent = 0;
    int answer = 0;
    int i = 0, j = 0;
    while (i < n || j < eligible_drinks) {
        long long price;
        if (i == n) {
            price = drinks[j++];
        } else if (j == eligible_drinks || desserts[i] <= drinks[j]) {
            price = desserts[i++];
        } else {
            price = drinks[j++];
        }
        if (spent + price > budget) break;
        spent += price;
        ++answer;
    }
    cout << answer << '\n';
}
