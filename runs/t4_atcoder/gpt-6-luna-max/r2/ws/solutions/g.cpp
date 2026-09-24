#include <bits/stdc++.h>
using namespace std;
using int64 = long long;

static const int MAXB = 60;
static const int64 NEG = numeric_limits<int64>::lowest() / 4;

// H[b][x][t]: maximum length of a non-increasing subsequence in
// popcount(0),...,popcount(2^b-1) that starts at x and ends at a value >= t.
int64 Htab[MAXB + 1][MAXB + 1][MAXB + 1];
bool monotone[MAXB + 1];

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // G[b][x][y]: best subsequence whose first value is exactly x
    // and whose last value is exactly y.
    static int64 G[MAXB + 1][MAXB + 1][MAXB + 1];
    for (int b = 0; b <= MAXB; ++b)
        for (int x = 0; x <= MAXB; ++x)
            for (int y = 0; y <= MAXB; ++y)
                G[b][x][y] = NEG;

    G[0][0][0] = 1;
    Htab[0][0][0] = 1;
    monotone[0] = true;

    for (int b = 1; b <= MAXB; ++b) {
        int64 gx[MAXB + 1][MAXB + 1];
        int64 gy[MAXB + 1][MAXB + 1];
        int64 prefY[MAXB + 1][MAXB + 1];
        for (int x = 0; x <= b; ++x) {
            for (int y = 0; y <= b; ++y) {
                gx[x][y] = NEG;
                gy[x][y] = NEG;
                prefY[x][y] = NEG;
            }
        }

        // First half is P_(b-1); second half is P_(b-1) with all
        // popcounts shifted up by one.
        for (int x = 0; x < b; ++x) {
            for (int y = 0; y <= x; ++y) {
                gx[x][y] = G[b - 1][x][y];
                gy[x + 1][y + 1] = G[b - 1][x][y];
            }
        }

        for (int y = 0; y <= b; ++y) {
            int64 best = NEG;
            for (int x = y; x <= b; ++x) {
                best = max(best, gy[x][y]);
                prefY[y][x] = best;
            }
        }

        for (int x = 0; x <= b; ++x) {
            for (int y = 0; y <= x; ++y) {
                int64 best = max(gx[x][y], gy[x][y]);
                for (int mid = y; mid <= x; ++mid) {
                    if (gx[x][mid] != NEG && prefY[y][mid] != NEG) {
                        best = max(best, gx[x][mid] + prefY[y][mid]);
                    }
                }
                G[b][x][y] = best;
            }
        }

        for (int x = 0; x <= b; ++x) {
            int64 best = NEG;
            for (int t = x; t >= 0; --t) {
                best = max(best, G[b][x][t]);
                Htab[b][x][t] = best;
            }
        }

        // Verify the anti-Monge property on the finite triangular domain.
        // This makes the column maxima searchable by divide and conquer.
        monotone[b] = true;
        for (int x1 = 0; x1 <= b && monotone[b]; ++x1) {
            for (int x2 = x1 + 1; x2 <= b && monotone[b]; ++x2) {
                for (int t1 = 0; t1 < x1 && monotone[b]; ++t1) {
                    for (int t2 = t1 + 1; t2 <= x1; ++t2) {
                        if (Htab[b][x1][t1] + Htab[b][x2][t2] <
                            Htab[b][x1][t2] + Htab[b][x2][t1]) {
                            monotone[b] = false;
                            break;
                        }
                    }
                }
            }
        }
    }

    int T;
    cin >> T;
    while (T--) {
        uint64_t L, R;
        cin >> L >> R;

        int64 dp[MAXB + 1] = {};
        while (L <= R) {
            uint64_t remain = R - L + 1;
            int byLength = 63 - __builtin_clzll(remain);
            int byAlignment = __builtin_ctzll(L);
            int b = min(byLength, byAlignment);
            uint64_t blockSize = uint64_t(1) << b;
            int c = __builtin_popcountll(L >> b);

            int64 best[MAXB + 1];
            for (int t = 0; t <= b; ++t) best[t] = NEG;

            if (monotone[b]) {
                function<void(int, int, int, int)> solve =
                    [&](int left, int right, int optLeft, int optRight) {
                        if (left > right) return;
                        int mid = (left + right) >> 1;
                        int lo = max(mid, optLeft);
                        int hi = optRight;
                        int bestX = lo;
                        int64 value = NEG;
                        for (int x = lo; x <= hi; ++x) {
                            int64 candidate = int64(dp[c + x]) + Htab[b][x][mid];
                            if (candidate > value) {
                                value = candidate;
                                bestX = x;
                            }
                        }
                        best[mid] = value;
                        solve(left, mid - 1, optLeft, bestX);
                        solve(mid + 1, right, bestX, optRight);
                    };
                solve(0, b, 0, b);
            } else {
                for (int t = 0; t <= b; ++t) {
                    for (int x = t; x <= b; ++x) {
                        best[t] = max(best[t],
                                      int64(dp[c + x]) + Htab[b][x][t]);
                    }
                }
            }

            for (int t = 0; t < c; ++t)
                dp[t] = max<int64>(dp[t], best[0]);
            for (int t = 0; t <= b; ++t)
                dp[c + t] = max<int64>(dp[c + t], best[t]);

            L += blockSize;
        }
        cout << dp[0] << '\n';
    }
    return 0;
}
