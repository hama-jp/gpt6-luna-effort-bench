#include <bits/stdc++.h>
using namespace std;

static constexpr int MAX_BITS = 60;
static constexpr long long NEG = LLONG_MIN / 4;
static long long best_block[MAX_BITS + 1][MAX_BITS + 1][MAX_BITS + 1];

static void precompute_blocks() {
    for (int b = 0; b <= MAX_BITS; ++b)
        for (int a = 0; a <= MAX_BITS; ++a)
            for (int s = 0; s <= MAX_BITS; ++s)
                best_block[b][a][s] = NEG;
    best_block[0][0][0] = 1;

    for (int b = 1; b <= MAX_BITS; ++b) {
        for (int a = 0; a < b; ++a) {
            for (int s = 0; s < b; ++s)
                best_block[b][a][s] = best_block[b - 1][a][s];

            long long suffix_best = NEG;
            for (int q = b - 2; q >= 0; --q) {
                suffix_best = max(suffix_best, best_block[b - 1][a][q + 1]);
                if (suffix_best == NEG) continue;
                for (int s = 1; s <= q + 1; ++s) {
                    long long second = best_block[b - 1][q][s - 1];
                    if (second != NEG)
                        best_block[b][a][s] = max(best_block[b][a][s], suffix_best + second);
                }
            }
        }

        for (int a = 1; a <= b; ++a) {
            for (int s = 1; s <= b; ++s) {
                best_block[b][a][s] = max(best_block[b][a][s], best_block[b - 1][a - 1][s - 1]);
            }
        }
    }
}

static void apply_block(array<long long, MAX_BITS + 1>& dp, int bits, int fixed_ones) {
    array<long long, MAX_BITS + 2> suffix{};
    suffix[MAX_BITS + 1] = NEG;
    for (int x = MAX_BITS; x >= 0; --x)
        suffix[x] = max(dp[x], suffix[x + 1]);

    vector<long long> before(bits + 1), result(bits + 1, NEG);
    for (int a = 0; a <= bits; ++a) {
        int threshold = fixed_ones + a;
        before[a] = (threshold <= MAX_BITS ? max(0LL, suffix[threshold]) : 0LL);
    }

    auto solve = [&](auto&& self, int left, int right, int opt_left, int opt_right) -> void {
        if (left > right) return;
        int mid = (left + right) / 2;
        int lo = max(mid, opt_left), hi = min(bits, opt_right);
        long long best = NEG;
        int best_a = lo;
        for (int a = lo; a <= hi; ++a) {
            long long inside = best_block[bits][a][mid];
            if (inside == NEG) continue;
            long long candidate = before[a] + inside;
            if (candidate >= best) {
                best = candidate;
                best_a = a;
            }
        }
        result[mid] = best;
        self(self, left, mid - 1, opt_left, best_a);
        self(self, mid + 1, right, best_a, opt_right);
    };
    solve(solve, 0, bits, 0, bits);

    for (int s = 0; s <= bits; ++s)
        dp[fixed_ones + s] = max(dp[fixed_ones + s], result[s]);
}

static long long solve_case(long long left, long long right) {
    array<long long, MAX_BITS + 1> dp;
    dp.fill(NEG);

    unsigned long long pos = (unsigned long long)left;
    unsigned long long end = (unsigned long long)right;
    while (pos <= end) {
        unsigned long long remaining = end - pos + 1;
        int bits = __builtin_ctzll(pos);
        while ((1ULL << bits) > remaining) --bits;
        while (bits < MAX_BITS && (pos % (1ULL << (bits + 1)) == 0) &&
               (1ULL << (bits + 1)) <= remaining) {
            ++bits;
        }
        int fixed_ones = __builtin_popcountll(pos >> bits);
        apply_block(dp, bits, fixed_ones);
        pos += (1ULL << bits);
    }

    return *max_element(dp.begin(), dp.end());
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    precompute_blocks();
    int t;
    cin >> t;
    while (t--) {
        long long l, r;
        cin >> l >> r;
        cout << solve_case(l, r) << '\n';
    }
}
