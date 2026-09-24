#include <bits/stdc++.h>
using namespace std;

struct Node {
    int mn, mnpos, mx, mxpos;
};

Node merge_node(const Node &a, const Node &b) {
    Node z;
    if (a.mn <= b.mn) z.mn = a.mn, z.mnpos = a.mnpos;
    else z.mn = b.mn, z.mnpos = b.mnpos;
    if (a.mx >= b.mx) z.mx = a.mx, z.mxpos = a.mxpos;
    else z.mx = b.mx, z.mxpos = b.mxpos;
    return z;
}

struct SegTree {
    int n;
    vector<Node> t;
    explicit SegTree(const vector<int> &a) {
        n = 1;
        while (n < (int)a.size()) n <<= 1;
        t.resize(2 * n);
        for (int i = 0; i < n; ++i) {
            int v = i < (int)a.size() ? a[i] : INT_MAX;
            int w = i < (int)a.size() ? a[i] : INT_MIN;
            t[n + i] = {v, i, w, i};
        }
        for (int i = n - 1; i; --i) t[i] = merge_node(t[i << 1], t[i << 1 | 1]);
    }
    Node query(int l, int r) {
        Node left{INT_MAX, -1, INT_MIN, -1}, right = left;
        for (l += n, r += n; l < r; l >>= 1, r >>= 1) {
            if (l & 1) left = merge_node(left, t[l++]);
            if (r & 1) right = merge_node(t[--r], right);
        }
        return merge_node(left, right);
    }
    void set_value(int p, int v) {
        p += n;
        t[p] = {v, p - n, v, p - n};
        for (p >>= 1; p; p >>= 1) t[p] = merge_node(t[p << 1], t[p << 1 | 1]);
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<int> p(n);
    for (int &v : p) cin >> v;
    SegTree st(p);
    while (m--) {
        int l, r;
        cin >> l >> r;
        --l;
        Node z = st.query(l, r);
        int x = z.mnpos, y = z.mxpos;
        if (x != y) {
            swap(p[x], p[y]);
            st.set_value(x, p[x]);
            st.set_value(y, p[y]);
        }
    }
    for (int i = 0; i < n; ++i) cout << p[i] << (i + 1 == n ? '\n' : ' ');
}
