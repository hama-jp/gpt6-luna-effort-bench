#include <bits/stdc++.h>
using namespace std;

struct Node {
    int mn, mnpos, mx, mxpos;
};
Node merge_node(const Node& a, const Node& b) {
    Node c;
    if (a.mn < b.mn || (a.mn == b.mn && a.mnpos < b.mnpos)) {
        c.mn = a.mn; c.mnpos = a.mnpos;
    } else {
        c.mn = b.mn; c.mnpos = b.mnpos;
    }
    if (a.mx > b.mx || (a.mx == b.mx && a.mxpos < b.mxpos)) {
        c.mx = a.mx; c.mxpos = a.mxpos;
    } else {
        c.mx = b.mx; c.mxpos = b.mxpos;
    }
    return c;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, M;
    cin >> N >> M;
    vector<int> P(N);
    for (int &x : P) cin >> x;

    int size = 1;
    while (size < N) size <<= 1;
    Node empty{INT_MAX, INT_MAX, INT_MIN, INT_MAX};
    vector<Node> seg(2 * size, empty);
    for (int i = 0; i < N; ++i) seg[size + i] = {P[i], i, P[i], i};
    for (int i = size - 1; i >= 1; --i) seg[i] = merge_node(seg[i << 1], seg[i << 1 | 1]);

    auto update = [&](int p) {
        int v = size + p;
        seg[v] = {P[p], p, P[p], p};
        for (v >>= 1; v; v >>= 1) seg[v] = merge_node(seg[v << 1], seg[v << 1 | 1]);
    };

    while (M--) {
        int l, r;
        cin >> l >> r;
        --l;
        Node left = empty, right = empty;
        int a = size + l, b = size + r;
        while (a < b) {
            if (a & 1) left = merge_node(left, seg[a++]);
            if (b & 1) right = merge_node(seg[--b], right);
            a >>= 1; b >>= 1;
        }
        Node q = merge_node(left, right);
        swap(P[q.mnpos], P[q.mxpos]);
        update(q.mnpos);
        update(q.mxpos);
    }

    for (int i = 0; i < N; ++i) {
        if (i) cout << ' ';
        cout << P[i];
    }
    cout << '\n';
    return 0;
}
