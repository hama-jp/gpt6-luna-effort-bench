#include <bits/stdc++.h>
using namespace std;
using int64 = long long;

static constexpr int64 NEG = -(1LL << 62);

struct Matrix {
    int d = 0;
    vector<int64> a;
    Matrix() = default;
    explicit Matrix(int n) : d(n), a((size_t)n * n, NEG) {}
    int64 &at(int r, int c) { return a[(size_t)r * d + c]; }
    int64 at(int r, int c) const { return a[(size_t)r * d + c]; }
};

static vector<int64> apply_matrix(const Matrix &m, const vector<int64> &v) {
    vector<int64> out(m.d, NEG);
    for (int i = 0; i < m.d; ++i) {
        int64 best = NEG;
        for (int j = i; j < m.d; ++j) {
            int64 x = v[j];
            if (x <= NEG / 2) continue;
            best = max(best, m.at(i, j) + x);
        }
        out[i] = best;
    }
    return out;
}

// The block transforms are Monge on their upper-triangular domain. Therefore
// the maximizing input column is nondecreasing as the output rank increases.
// Divide-and-conquer optimization applies a transform in O(d log d).
static vector<int64> apply_block(const Matrix &m, const vector<int64> &v, int active) {
    vector<int64> out(m.d, NEG);
    function<void(int, int, int, int)> solve = [&](int ql, int qr, int optl, int optr) {
        if (ql > qr) return;
        int mid = (ql + qr) / 2;
        int lo = max(mid, optl);
        int best_col = lo;
        int64 best = NEG;
        for (int j = lo; j <= optr; ++j) {
            if (v[j] <= NEG / 2) continue;
            int64 candidate = m.at(mid, j) + v[j];
            if (candidate > best) {
                best = candidate;
                best_col = j;
            }
        }
        out[mid] = best;
        solve(ql, mid - 1, optl, best_col);
        solve(mid + 1, qr, best_col, optr);
    };
    solve(0, active - 1, 0, m.d - 1);
    out[active] = v[active]; // The boundary suffix is unchanged by the block.
    return out;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // For a block [q*2^b, (q+1)*2^b), popcounts are
    // popcount(q) + popcount(0..2^b-1). Store its max-plus DP transform.
    vector<vector<Matrix>> block(61);
    for (int h = 0; h <= 60; ++h) {
        Matrix base(2);
        base.at(0, 0) = 1;
        base.at(0, 1) = 1;
        base.at(1, 1) = 0;
        block[0].push_back(move(base));
    }

    for (int b = 1; b <= 60; ++b) {
        block[b].resize(61 - b);
        const int d = b + 2;
        for (int h = 0; h + b <= 60; ++h) {
            const Matrix &left = block[b - 1][h];
            const Matrix &right = block[b - 1][h + 1];
            Matrix cur(d);
            for (int col = 0; col < d; ++col) {
                vector<int64> lv(b + 1, NEG);
                for (int i = 0; i < b; ++i) if (i == col) lv[i] = 0;
                if (col == b || col == b + 1) lv[b] = 0;
                vector<int64> lo = apply_matrix(left, lv);

                vector<int64> rv(b + 1, NEG);
                for (int i = 0; i < b - 1; ++i) rv[i] = lo[i + 1];
                if (col == b) rv[b - 1] = 0;
                if (col == b + 1) rv[b] = 0;
                vector<int64> ro = apply_matrix(right, rv);

                cur.at(0, col) = lo[0];
                for (int i = 0; i < b; ++i) cur.at(i + 1, col) = ro[i];
                if (col == b + 1) cur.at(b + 1, col) = 0;
            }
            block[b][h] = move(cur);
        }
    }

    int t;
    cin >> t;
    while (t--) {
        uint64_t l, r;
        cin >> l >> r;
        array<int64, 61> dp{}; // Empty subsequences are available at every rank.

        uint64_t cur = l;
        while (cur <= r) {
            uint64_t remain = r - cur + 1;
            int b = 63 - __builtin_clzll(remain);
            if (cur != 0) b = min(b, __builtin_ctzll(cur));

            int h = __builtin_popcountll(cur >> b);
            int d = b + 2;
            vector<int64> v(d);
            for (int i = 0; i <= b; ++i) v[i] = dp[h + i];
            int64 ext = NEG;
            for (int i = h + b + 1; i <= 60; ++i) ext = max(ext, dp[i]);
            v[b + 1] = ext;
            vector<int64> out = apply_block(block[b][h], v, b + 1);
            for (int i = 0; i <= b; ++i) dp[h + i] = out[i];

            cur += (1ULL << b);
        }

        cout << *max_element(dp.begin(), dp.end()) << '\n';
    }
}
