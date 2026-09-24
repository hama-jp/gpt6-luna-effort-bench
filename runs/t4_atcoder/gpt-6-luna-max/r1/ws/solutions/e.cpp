#include <bits/stdc++.h>
using namespace std;

struct SegmentTree {
    int size;
    vector<int> mn, mx;

    explicit SegmentTree(const vector<int>& a) {
        size = 1;
        while (size < (int)a.size()) size <<= 1;
        mn.assign(2 * size, INT_MAX);
        mx.assign(2 * size, INT_MIN);
        for (int i = 0; i < (int)a.size(); ++i) {
            mn[size + i] = mx[size + i] = a[i];
        }
        for (int i = size - 1; i; --i) {
            mn[i] = min(mn[2 * i], mn[2 * i + 1]);
            mx[i] = max(mx[2 * i], mx[2 * i + 1]);
        }
    }

    pair<int, int> query(int left, int right) const {
        int low = INT_MAX, high = INT_MIN;
        for (left += size, right += size; left < right; left >>= 1, right >>= 1) {
            if (left & 1) {
                low = min(low, mn[left]);
                high = max(high, mx[left++]);
            }
            if (right & 1) {
                --right;
                low = min(low, mn[right]);
                high = max(high, mx[right]);
            }
        }
        return {low, high};
    }

    void update(int pos, int value) {
        int p = size + pos;
        mn[p] = mx[p] = value;
        for (p >>= 1; p; p >>= 1) {
            mn[p] = min(mn[2 * p], mn[2 * p + 1]);
            mx[p] = max(mx[2 * p], mx[2 * p + 1]);
        }
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> p(n), position(n + 1);
    for (int i = 0; i < n; ++i) {
        cin >> p[i];
        position[p[i]] = i;
    }
    SegmentTree seg(p);

    while (m--) {
        int l, r;
        cin >> l >> r;
        --l;
        auto [smallest, largest] = seg.query(l, r);
        int a = position[smallest], b = position[largest];
        swap(p[a], p[b]);
        position[p[a]] = a;
        position[p[b]] = b;
        seg.update(a, p[a]);
        seg.update(b, p[b]);
    }

    for (int i = 0; i < n; ++i) {
        if (i) cout << ' ';
        cout << p[i];
    }
    cout << '\n';
}
