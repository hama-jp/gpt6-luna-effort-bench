#include <bits/stdc++.h>
using namespace std;
using int64 = long long;

static constexpr int MAXK = 60;
static constexpr int64 NEG = LLONG_MIN / 4;
static int64 trans[MAXK + 1][MAXK + 1][MAXK + 1];

// For every column z, find the row u maximizing w[u] + trans[k][u][z].
// The triangular max-plus matrices trans[k] are Monge, so the row maxima
// are monotone and SMAWK finds them in linear time.
template <class Value>
void smawk(const vector<int> &rows, const vector<int> &cols,
           Value &value, vector<int> &answer) {
    if (rows.empty()) return;

    vector<int> reduced;
    reduced.reserve(min(rows.size(), cols.size()));
    for (int col : cols) {
        while (!reduced.empty()) {
            int row = rows[reduced.size() - 1];
            if (value(row, col) > value(row, reduced.back())) reduced.pop_back();
            else break;
        }
        if (reduced.size() < rows.size()) reduced.push_back(col);
    }

    vector<int> odd_rows;
    odd_rows.reserve(rows.size() / 2);
    for (int i = 1; i < (int)rows.size(); i += 2) odd_rows.push_back(rows[i]);
    smawk(odd_rows, reduced, value, answer);

    for (int i = 0; i < (int)rows.size(); i += 2) {
        int begin = 0;
        int end = (int)reduced.size() - 1;
        if (i > 0) {
            begin = lower_bound(reduced.begin(), reduced.end(), answer[rows[i - 1]]) - reduced.begin();
        }
        if (i + 1 < (int)rows.size()) {
            end = lower_bound(reduced.begin(), reduced.end(), answer[rows[i + 1]]) - reduced.begin();
        }
        int best_col = reduced[begin];
        int64 best_value = value(rows[i], best_col);
        for (int j = begin + 1; j <= end; ++j) {
            int64 cur = value(rows[i], reduced[j]);
            if (cur > best_value) {
                best_value = cur;
                best_col = reduced[j];
            }
        }
        answer[rows[i]] = best_col;
    }
}

void build_transitions() {
    for (int k = 0; k <= MAXK; ++k)
        for (int a = 0; a <= MAXK; ++a)
            for (int b = 0; b <= MAXK; ++b)
                trans[k][a][b] = NEG;
    // The sequence for k=0 is [popcount(0)] = [0].
    trans[0][0][0] = 1;

    for (int k = 1; k <= MAXK; ++k) {
        int64 first[MAXK + 1][MAXK + 1], second[MAXK + 1][MAXK + 1];
        for (int a = 0; a <= k; ++a)
            for (int b = 0; b <= k; ++b)
                first[a][b] = second[a][b] = NEG;
        for (int a = 0; a <= k; ++a) first[a][a] = second[a][a] = 0;

        // First half: popcounts 0..2^(k-1)-1.
        for (int a = 0; a < k; ++a)
            for (int b = 0; b < k; ++b)
                first[a][b] = max(first[a][b], trans[k - 1][a][b]);
        // A previous value k permits every value in the first half.
        for (int b = 0; b < k; ++b)
            first[k][b] = trans[k - 1][k - 1][b];

        // Second half: the same sequence with every popcount increased by 1.
        for (int a = 1; a <= k; ++a) {
            int old_row = min(a - 1, k - 1);
            for (int b = 0; b < k; ++b)
                second[a][b + 1] = max(second[a][b + 1], trans[k - 1][old_row][b]);
        }

        // Concatenate the two halves with max-plus matrix multiplication.
        for (int a = 0; a <= k; ++a) {
            for (int mid = 0; mid <= k; ++mid) {
                if (first[a][mid] == NEG) continue;
                for (int b = 0; b <= k; ++b) {
                    if (second[mid][b] == NEG) continue;
                    trans[k][a][b] = max(trans[k][a][b], first[a][mid] + second[mid][b]);
                }
            }
        }
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    build_transitions();
    int t;
    cin >> t;
    while (t--) {
        int64 left, right;
        cin >> left >> right;
        array<int64, MAXK + 1> dp;
        dp.fill(0); // virtual previous values allow a subsequence to start anywhere

        int64 cur = left;
        while (cur <= right) {
            int by_alignment = __builtin_ctzll((unsigned long long)cur);
            int64 remaining = right - cur + 1;
            int by_length = 63 - __builtin_clzll((unsigned long long)remaining);
            int k = min(by_alignment, by_length);
            int64 block_size = 1LL << k;
            int c = __builtin_popcountll((unsigned long long)(cur >> k));

            array<int64, MAXK + 1> w;
            w.fill(NEG);
            for (int u = 0; u < k; ++u) w[u] = dp[c + u];
            for (int v = c + k; v <= MAXK; ++v) w[k] = max(w[k], dp[v]);

            auto value = [&](int z, int u) -> int64 {
                if (u < z || w[u] == NEG || trans[k][u][z] == NEG) return NEG;
                return w[u] + trans[k][u][z];
            };
            vector<int> rows(k + 1), cols(k + 1), best(k + 1);
            iota(rows.begin(), rows.end(), 0); // output popcount z
            iota(cols.begin(), cols.end(), 0); // incoming threshold u
            smawk(rows, cols, value, best);

            auto next = dp;
            for (int z = 0; z <= k; ++z) {
                int u = best[z];
                next[c + z] = max(next[c + z], w[u] + trans[k][u][z]);
            }
            dp = next;
            cur += block_size;
        }

        cout << *max_element(dp.begin(), dp.end()) << '\n';
    }
}
