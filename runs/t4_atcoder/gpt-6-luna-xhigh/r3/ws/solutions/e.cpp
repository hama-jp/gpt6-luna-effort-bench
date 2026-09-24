#include <bits/stdc++.h>
using namespace std;

struct Node {
    int mn, mn_pos, mx, mx_pos;
};

Node merge_node(const Node &a, const Node &b) {
    Node r;
    if (a.mn <= b.mn) r.mn = a.mn, r.mn_pos = a.mn_pos;
    else r.mn = b.mn, r.mn_pos = b.mn_pos;
    if (a.mx >= b.mx) r.mx = a.mx, r.mx_pos = a.mx_pos;
    else r.mx = b.mx, r.mx_pos = b.mx_pos;
    return r;
}

struct SegTree {
    int n;
    vector<Node> t;
    SegTree(const vector<int> &a) : n((int)a.size()), t(4 * a.size()) { build(1, 0, n, a); }
    void build(int v, int l, int r, const vector<int> &a) {
        if (r - l == 1) {
            t[v] = {a[l], l, a[l], l};
            return;
        }
        int m = (l + r) / 2;
        build(v * 2, l, m, a);
        build(v * 2 + 1, m, r, a);
        t[v] = merge_node(t[v * 2], t[v * 2 + 1]);
    }
    Node query(int v, int l, int r, int ql, int qr) {
        if (ql <= l && r <= qr) return t[v];
        int m = (l + r) / 2;
        if (qr <= m) return query(v * 2, l, m, ql, qr);
        if (ql >= m) return query(v * 2 + 1, m, r, ql, qr);
        return merge_node(query(v * 2, l, m, ql, qr), query(v * 2 + 1, m, r, ql, qr));
    }
    Node query(int l, int r) { return query(1, 0, n, l, r); }
    void update(int v, int l, int r, int p, int value) {
        if (r - l == 1) {
            t[v] = {value, p, value, p};
            return;
        }
        int m = (l + r) / 2;
        if (p < m) update(v * 2, l, m, p, value);
        else update(v * 2 + 1, m, r, p, value);
        t[v] = merge_node(t[v * 2], t[v * 2 + 1]);
    }
    void update(int p, int value) { update(1, 0, n, p, value); }
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
        swap(p[z.mn_pos], p[z.mx_pos]);
        st.update(z.mn_pos, p[z.mn_pos]);
        st.update(z.mx_pos, p[z.mx_pos]);
    }
    for (int i = 0; i < n; ++i) {
        if (i) cout << ' ';
        cout << p[i];
    }
    cout << '\n';
}
