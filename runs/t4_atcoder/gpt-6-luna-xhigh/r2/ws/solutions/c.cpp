#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    priority_queue<long long, vector<long long>, greater<long long>> top3;
    for (int i = 0; i < n; ++i) {
        long long x;
        cin >> x;
        top3.push(x);
        if (top3.size() > 3) top3.pop();
        if (i >= 2) cout << top3.top() << '\n';
    }
}
