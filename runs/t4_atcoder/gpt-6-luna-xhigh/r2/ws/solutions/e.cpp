#include <bits/stdc++.h>
using namespace std;

struct Node {
    int min_value, min_pos;
    int max_value, max_pos;
};

Node merge_node(const Node &a, const Node &b) {
    Node r;
    if (a.min_value < b.min_value) {
        r.min_value = a.min_value;
        r.min_pos = a.min_pos;
    } else {
        r.min_value = b.min_value;
        r.min_pos = b.min_pos;
    }
    if (a.max_value > b.max_value) {
        r.max_value = a.max_value;
        r.max_pos = a.max_pos;
    } else {
        r.max_value = b.max_value;
        r.max_pos = b.max_pos;
    }
    return r;
}

struct SegTree {
    int size;
    vector<Node> tree;
    explicit SegTree(const vector<int> &a) {
        size = 1;
        while (size < (int)a.size()) size <<= 1;
        tree.resize(2 * size);
        for (int i = 0; i < (int)a.size(); ++i) tree[size + i] = {a[i], i, a[i], i};
        for (int i = size - 1; i >= 1; --i) tree[i] = merge_node(tree[2 * i], tree[2 * i + 1]);
    }
    void set_value(int p, int value) {
        p += size;
        tree[p] = {value, p - size, value, p - size};
        for (p >>= 1; p; p >>= 1) tree[p] = merge_node(tree[2 * p], tree[2 * p + 1]);
    }
    Node query(int l, int r) const { // half-open
        Node left{INT_MAX, -1, INT_MIN, -1};
        Node right{INT_MAX, -1, INT_MIN, -1};
        for (l += size, r += size; l < r; l >>= 1, r >>= 1) {
            if (l & 1) left = merge_node(left, tree[l++]);
            if (r & 1) right = merge_node(tree[--r], right);
        }
        return merge_node(left, right);
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> p(n);
    for (int &v : p) cin >> v;
    SegTree seg(p);

    for (int q = 0; q < m; ++q) {
        int l, r;
        cin >> l >> r;
        --l;
        Node z = seg.query(l, r);
        int x = p[z.min_pos], y = p[z.max_pos];
        swap(p[z.min_pos], p[z.max_pos]);
        seg.set_value(z.min_pos, p[z.min_pos]);
        seg.set_value(z.max_pos, p[z.max_pos]);
    }

    for (int i = 0; i < n; ++i) {
        if (i) cout << ' ';
        cout << p[i];
    }
    cout << '\n';
}
