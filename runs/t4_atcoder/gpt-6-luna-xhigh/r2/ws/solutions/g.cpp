#include <bits/stdc++.h>
using namespace std;

static constexpr long long NEG = -(1LL << 60);
static long long trans[61][61][61];

void build_transitions() {
    for (int k = 0; k <= 60; ++k)
        for (int i = 0; i <= 60; ++i)
            for (int j = 0; j <= 60; ++j)
                trans[k][i][j] = NEG;

    // The block for k=0 contains only the value 0.
    trans[0][0][0] = 1;

    for (int k = 1; k <= 60; ++k) {
        long long first[61][61], second[61][61];
        for (int i = 0; i <= k; ++i)
            for (int j = 0; j <= k; ++j)
                first[i][j] = second[i][j] = NEG;

        // First half: the previous block on values 0..k-1.
        for (int i = 0; i < k; ++i)
            for (int j = 0; j <= i; ++j)
                first[i][j] = trans[k - 1][i][j];
        for (int j = 0; j < k; ++j)
            first[k][j] = trans[k - 1][k - 1][j];
        first[k][k] = 0; // level k is untouched in the first half

        // Second half: the previous block shifted up by one.
        second[0][0] = 0; // values in this half are all at least 1
        for (int i = 1; i <= k; ++i)
            for (int j = 1; j <= i; ++j)
                second[i][j] = trans[k - 1][i - 1][j - 1];

        // Compose the two max-plus transitions.
        for (int i = 0; i <= k; ++i) {
            for (int j = 0; j <= i; ++j) {
                long long best = NEG;
                for (int mid = j; mid <= i; ++mid) {
                    if (first[i][mid] == NEG || second[mid][j] == NEG) continue;
                    best = max(best, first[i][mid] + second[mid][j]);
                }
                trans[k][i][j] = best;
            }
        }
    }
}

void divide_conquer_max(int left, int right, int opt_left, int opt_right,
                        int k, const long long row_value[61],
                        long long result[61]) {
    if (left > right) return;
    int mid = (left + right) / 2;
    long long best = NEG;
    int best_row = max(mid, opt_left);
    int end = min(k, opt_right);
    for (int row = best_row; row <= end; ++row) {
        if (row_value[row] == NEG || trans[k][row][mid] == NEG) continue;
        long long candidate = row_value[row] + trans[k][row][mid];
        if (candidate > best) {
            best = candidate;
            best_row = row;
        }
    }
    result[mid] = best;
    divide_conquer_max(left, mid - 1, opt_left, best_row, k, row_value, result);
    divide_conquer_max(mid + 1, right, best_row, opt_right, k, row_value, result);
}

void apply_block(long long dp[61], int shift, int k) {
    long long old[61];
    copy(dp, dp + 61, old);

    long long row_value[61], result[61];
    for (int r = 0; r <= k; ++r) row_value[r] = NEG;
    for (int r = 0; r < k; ++r) row_value[r] = old[shift + r];
    for (int x = shift + k; x <= 60; ++x)
        row_value[k] = max(row_value[k], old[x]);

    divide_conquer_max(0, k, 0, k, k, row_value, result);
    for (int b = 0; b <= k; ++b)
        dp[shift + b] = max(dp[shift + b], result[b]);
}

long long solve(long long left, long long right) {
    long long dp[61];
    fill(dp, dp + 61, NEG);
    // An empty subsequence ending above every possible popcount lets a chain
    // start at any element in the interval.
    dp[60] = 0;

    long long current = left;
    while (current <= right) {
        long long remaining = right - current + 1;
        int align = __builtin_ctzll((unsigned long long)current);
        int by_length = 63 - __builtin_clzll((unsigned long long)remaining);
        int k = min(align, by_length);
        long long quotient = current >> k;
        int shift = __builtin_popcountll((unsigned long long)quotient);
        apply_block(dp, shift, k);
        current += 1LL << k;
    }

    return *max_element(dp, dp + 61);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    build_transitions();
    int t;
    cin >> t;
    while (t--) {
        long long l, r;
        cin >> l >> r;
        cout << solve(l, r) << '\n';
    }
}
