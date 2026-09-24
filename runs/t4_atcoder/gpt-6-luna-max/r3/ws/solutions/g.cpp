#include <bits/stdc++.h>
using namespace std;

using int64 = long long;
static constexpr int MAX_RANK = 60;
static constexpr int SENTINEL = 61;
static constexpr int DIM = 62;
static constexpr int64 NEG = -(1LL << 62);

using Matrix = array<array<int64, DIM>, DIM>;
static Matrix transfer[61];

static Matrix identity_matrix() {
    Matrix a;
    for (int i = 0; i < DIM; ++i) {
        for (int j = 0; j < DIM; ++j) a[i][j] = (i == j ? 0 : NEG);
    }
    return a;
}

static Matrix multiply(const Matrix &a, const Matrix &b) {
    Matrix c;
    for (int i = 0; i < DIM; ++i) c[i].fill(NEG);
    for (int i = 0; i < DIM; ++i) {
        for (int k = i; k < DIM; ++k) {
            if (a[i][k] == NEG) continue;
            for (int j = k; j < DIM; ++j) {
                if (b[k][j] == NEG) continue;
                c[i][j] = max(c[i][j], a[i][k] + b[k][j]);
            }
        }
    }
    return c;
}

static int current_k, current_offset;
static const vector<int64> *current_dp;

static inline int64 matrix_value(int row, int col) {
    int normal_max = MAX_RANK - current_offset;
    int local_col;
    int source_rank;
    if (col <= normal_max) {
        local_col = col;
        source_rank = current_offset + local_col;
    } else {
        local_col = SENTINEL;
        source_rank = SENTINEL;
    }
    int64 coefficient = transfer[current_k][row][local_col];
    if (coefficient == NEG || (*current_dp)[source_rank] == NEG) return NEG;
    return coefficient + (*current_dp)[source_rank];
}

static void smawk(const vector<int> &rows, const vector<int> &cols, vector<int> &answer_col) {
    if (rows.empty()) return;
    if (rows.size() == 1) {
        int best = cols[0];
        int64 best_value = matrix_value(rows[0], best);
        for (size_t j = 1; j < cols.size(); ++j) {
            int64 value = matrix_value(rows[0], cols[j]);
            if (value > best_value) {
                best_value = value;
                best = cols[j];
            }
        }
        answer_col[rows[0]] = best;
        return;
    }

    vector<int> reduced;
    reduced.reserve(min(rows.size(), cols.size()));
    for (int col : cols) {
        while (!reduced.empty()) {
            int row = rows[reduced.size() - 1];
            if (matrix_value(row, col) > matrix_value(row, reduced.back())) {
                reduced.pop_back();
            } else {
                break;
            }
        }
        if (reduced.size() < rows.size()) reduced.push_back(col);
    }

    vector<int> odd_rows;
    odd_rows.reserve(rows.size() / 2);
    for (size_t i = 1; i < rows.size(); i += 2) odd_rows.push_back(rows[i]);
    smawk(odd_rows, reduced, answer_col);

    for (size_t i = 0; i < rows.size(); i += 2) {
        size_t lo = 0;
        size_t hi = reduced.size() - 1;
        if (i > 0) {
            lo = lower_bound(reduced.begin(), reduced.end(), answer_col[rows[i - 1]]) - reduced.begin();
        }
        if (i + 1 < rows.size()) {
            hi = lower_bound(reduced.begin(), reduced.end(), answer_col[rows[i + 1]]) - reduced.begin();
        }

        int best = reduced[lo];
        int64 best_value = matrix_value(rows[i], best);
        for (size_t j = lo + 1; j <= hi; ++j) {
            int64 value = matrix_value(rows[i], reduced[j]);
            if (value > best_value) {
                best_value = value;
                best = reduced[j];
            }
        }
        answer_col[rows[i]] = best;
    }
}

static void apply_block(vector<int64> &dp, int offset, int k) {
    if (k == 0) {
        int64 best = dp[SENTINEL];
        for (int rank = offset; rank <= MAX_RANK; ++rank) best = max(best, dp[rank]);
        dp[offset] = best + 1;
        return;
    }

    current_k = k;
    current_offset = offset;
    current_dp = &dp;

    vector<int> rows(k + 1), cols(MAX_RANK - offset + 2), answer_col(k + 1, -1);
    iota(rows.begin(), rows.end(), 0);
    iota(cols.begin(), cols.end(), 0); // normal local ranks, then the sentinel

    smawk(rows, cols, answer_col);

    vector<int64> updated(k + 1);
    for (int i = 0; i <= k; ++i) updated[i] = matrix_value(i, answer_col[i]);
    for (int i = 0; i <= k; ++i) dp[offset + i] = updated[i];
}

static int floor_log2_u64(uint64_t x) {
    return 63 - __builtin_clzll(x);
}

static void process_suffix(vector<int64> &dp, uint64_t low, int h, int offset) {
    uint64_t limit = 1ULL << h;
    uint64_t x = low;
    while (x < limit) {
        uint64_t remaining = limit - x;
        int k = floor_log2_u64(remaining);
        if (x != 0) k = min(k, __builtin_ctzll(x));
        int block_offset = offset + __builtin_popcountll(x >> k);
        apply_block(dp, block_offset, k);
        x += 1ULL << k;
    }
}

static void process_prefix(vector<int64> &dp, uint64_t high, int h, int offset) {
    uint64_t x = 0;
    uint64_t remaining = high + 1;
    while (remaining > 0) {
        int k = floor_log2_u64(remaining);
        int block_offset = offset + __builtin_popcountll(x >> k);
        apply_block(dp, block_offset, k);
        uint64_t length = 1ULL << k;
        x += length;
        remaining -= length;
    }
}

static void build_transfers() {
    transfer[0] = identity_matrix();
    for (int j = 0; j < DIM; ++j) transfer[0][0][j] = 1;

    for (int k = 1; k <= MAX_RANK; ++k) {
        Matrix second = identity_matrix();
        // Shift every rank in the second half upward by one. The sentinel
        // stays at SENTINEL; local rank 60 would shift out of the domain.
        for (int i = 0; i < k; ++i) {
            int row = i + 1;
            for (int j = 0; j < MAX_RANK; ++j) {
                second[row][j + 1] = transfer[k - 1][i][j];
            }
            second[row][SENTINEL] = transfer[k - 1][i][SENTINEL];
        }
        transfer[k] = multiply(second, transfer[k - 1]);
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    build_transfers();
    int t;
    cin >> t;
    while (t--) {
        uint64_t l, r;
        cin >> l >> r;
        if (l == r) {
            cout << 1 << '\n';
            continue;
        }

        uint64_t diff = l ^ r;
        int h = floor_log2_u64(diff);
        uint64_t low_mask = (1ULL << (h + 1)) - 1;
        uint64_t base = l & ~low_mask;
        uint64_t left_low = l - base;
        uint64_t right_start = base + (1ULL << h);
        uint64_t right_high = r - right_start;
        int base_popcount = __builtin_popcountll(base);

        vector<int64> dp(DIM, NEG);
        dp[SENTINEL] = 0;
        process_suffix(dp, left_low, h, base_popcount);
        process_prefix(dp, right_high, h, base_popcount + 1);

        int64 answer = 0;
        for (int rank = 0; rank <= MAX_RANK; ++rank) answer = max(answer, dp[rank]);
        cout << answer << '\n';
    }
    return 0;
}
