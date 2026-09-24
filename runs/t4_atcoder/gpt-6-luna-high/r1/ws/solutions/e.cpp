#include <bits/stdc++.h>
using namespace std;
struct Node{int mn,mx,imn,imx;};
struct Seg{
 int n; vector<Node> t;
 Seg(vector<int>&a):n(a.size()),t(4*a.size()){build(1,0,n,a);}
 Node merge(Node a,Node b){ Node r; if(a.mn<=b.mn)r.mn=a.mn,r.imn=a.imn;else r.mn=b.mn,r.imn=b.imn; if(a.mx>=b.mx)r.mx=a.mx,r.imx=a.imx;else r.mx=b.mx,r.imx=b.imx; return r; }
 void build(int v,int l,int r,vector<int>&a){if(r-l==1){t[v]={a[l],a[l],l,l};return;}int m=(l+r)/2;build(v*2,l,m,a);build(v*2+1,m,r,a);t[v]=merge(t[v*2],t[v*2+1]);}
 Node query(int v,int l,int r,int ql,int qr){if(ql<=l&&r<=qr)return t[v];int m=(l+r)/2;if(qr<=m)return query(v*2,l,m,ql,qr);if(ql>=m)return query(v*2+1,m,r,ql,qr);return merge(query(v*2,l,m,ql,qr),query(v*2+1,m,r,ql,qr));}
 Node query(int l,int r){return query(1,0,n,l,r);}
 void setv(int v,int l,int r,int p,int x){if(r-l==1){t[v]={x,x,l,l};return;}int m=(l+r)/2;if(p<m)setv(v*2,l,m,p,x);else setv(v*2+1,m,r,p,x);t[v]=merge(t[v*2],t[v*2+1]);}
 void setv(int p,int x){setv(1,0,n,p,x);}
};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;vector<int>a(n);for(int&x:a)cin>>x;Seg st(a);while(m--){int l,r;cin>>l>>r;--l;Node q=st.query(l,r);st.setv(q.imn,q.mx);st.setv(q.imx,q.mn);}for(int i=0;i<n;i++)cout<<st.query(i,i+1).mn<<(i+1==n?'\n':' ');}
