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
    explicit SegTree(const vector<int> &p) {
        size = 1;
        while (size < (int)p.size()) size <<= 1;
        tree.resize(2 * size);
        for (int i = 0; i < size; ++i) {
            if (i < (int)p.size()) tree[size + i] = {p[i], i, p[i], i};
            else tree[size + i] = {INT_MAX, -1, INT_MIN, -1};
        }
        for (int i = size - 1; i > 0; --i) tree[i] = merge_node(tree[2 * i], tree[2 * i + 1]);
    }
    void set_value(int pos, int value) {
        int i = size + pos;
        tree[i] = {value, pos, value, pos};
        while (i >>= 1) tree[i] = merge_node(tree[2 * i], tree[2 * i + 1]);
    }
    Node query(int left, int right) const { // [left, right)
        Node l = {INT_MAX, -1, INT_MIN, -1};
        Node r = {INT_MAX, -1, INT_MIN, -1};
        for (left += size, right += size; left < right; left >>= 1, right >>= 1) {
            if (left & 1) l = merge_node(l, tree[left++]);
            if (right & 1) r = merge_node(tree[--right], r);
        }
        return merge_node(l, r);
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

    while (m--) {
        int l, r;
        cin >> l >> r;
        --l;
        Node q = seg.query(l, r);
        int i = q.min_pos, j = q.max_pos;
        swap(p[i], p[j]);
        seg.set_value(i, p[i]);
        seg.set_value(j, p[j]);
    }

    for (int i = 0; i < n; ++i) {
        if (i) cout << ' ';
        cout << p[i];
    }
    cout << '\n';
    return 0;
}
