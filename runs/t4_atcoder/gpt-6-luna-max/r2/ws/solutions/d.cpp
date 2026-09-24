#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, M;
    long long K, X, Y;
    cin >> N >> M >> K;
    cin >> X >> Y;

    vector<long long> A(N), B(M);
    for (auto &x : A) cin >> x;
    for (auto &x : B) cin >> x;

    sort(A.begin(), A.end());
    sort(B.begin(), B.end());

    vector<long long> prefA(N + 1, 0), prefB(M + 1, 0), prefQ(M + 1, 0);
    for (int i = 0; i < N; ++i) prefA[i + 1] = prefA[i] + A[i];
    for (int i = 0; i < M; ++i) {
        prefB[i + 1] = prefB[i] + B[i];
        prefQ[i + 1] = prefQ[i] + (B[i] + K - 1) / K;
    }

    const long long cash = X + Y * K;
    int ans = 0;
    for (int r = 0; r <= M; ++r) {
        if (prefQ[r] > Y) break;
        long long remain = cash - prefB[r];
        int d = upper_bound(prefA.begin(), prefA.end(), remain) - prefA.begin() - 1;
        d = max(d, 0);
        ans = max(ans, r + d);
    }
    cout << ans << '\n';
    return 0;
}
