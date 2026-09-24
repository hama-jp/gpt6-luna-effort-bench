#include <bits/stdc++.h>
using namespace std;
using int64 = long long;

struct Agg {
    int64 w = 0;
    int64 wx = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N;
    int64 M;
    cin >> N >> M;
    vector<int64> A(N), B(N);
    for (auto &x : A) cin >> x;
    for (auto &x : B) cin >> x;

    vector<Agg> sumDiag(2 * N + 1);
    vector<Agg> diffDiag(2 * N + 1);
    const int off = N - 1;

    for (int r = 1; r <= N; ++r) {
        for (int c = 1; c <= N; ++c) {
            int64 w = (A[r - 1] * B[c - 1]) % M;
            int s = r + c;
            int d = r - c + off;
            sumDiag[s].w += w;
            sumDiag[s].wx += w * s;
            diffDiag[d].w += w;
            diffDiag[d].wx += w * (r - c);
        }
    }

    auto make_prefix = [](vector<Agg>& v) {
        for (size_t i = 1; i < v.size(); ++i) {
            v[i].w += v[i - 1].w;
            v[i].wx += v[i - 1].wx;
        }
    };
    make_prefix(sumDiag);
    make_prefix(diffDiag);

    int64 totalW = sumDiag.back().w;
    int64 totalSum = sumDiag.back().wx;
    int64 totalDiff = diffDiag.back().wx;

    auto abs_sum = [](const vector<Agg>& pref, int idx, int64 x,
                      int64 totalW, int64 totalWX) -> int64 {
        int64 leftW = pref[idx].w;
        int64 leftWX = pref[idx].wx;
        return x * leftW - leftWX + (totalWX - leftWX) - x * (totalW - leftW);
    };

    int64 answer = 0;
    for (int i = 1; i <= N; ++i) {
        for (int j = 1; j <= N; ++j) {
            int s = i + j;
            int d = i - j;
            int64 val = abs_sum(sumDiag, s, s, totalW, totalSum)
                      + abs_sum(diffDiag, d + off, d, totalW, totalDiff);
            int64 f = val / 2;
            int64 cur = f + int64(i - 1) * N + (j - 1);
            answer ^= cur;
        }
    }

    cout << answer << '\n';
    return 0;
}
