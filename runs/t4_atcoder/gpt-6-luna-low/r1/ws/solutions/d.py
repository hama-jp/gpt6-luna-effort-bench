import sys
input = sys.stdin.readline
n, m, k = map(int, input().split())
x, y = map(int, input().split())
a = list(map(int, input().split()))
b = list(map(int, input().split()))
# For each chosen dessert, optimal payment with k-notes costs ceil(A/K)
# notes and leaves change, requiring exactly max(0,A-K*notes?) ones.
# Instead let each purchase consume q K notes and balance with ones; dessert
# can be paid using q=floor(A/K) with remainder ones, or ceil with change.
# The required one-note net consumption is A mod K when paying floor notes,
# or 0 when enough ceil-note change can be returned only as ones (needs K-r ones back).
# enumerate desserts by residue and use standard top-k resource formulation.
def feasible(cnt, desserts):
    # choose cnt cheapest dessert costs in ones after using K notes optimally;
    # each dessert i consumes floor(A/K) K notes plus remainder in ones.
    return False
# Sort all items by their K-note requirement. For any chosen set, K notes fund
# floor(price/K) notes for desserts and ceil(price/K) for drinks; remaining
# price portions are settled in ones. Use binary search over count and greedy.
# Convert each item's payment into minimum K notes, then residual one-note need.
des = sorted(((v // k, v % k) for v in a))
dr = sorted(((v + k - 1) // k, 0) for v in b)
# Select products by K-note counts; for fixed number choose cheapest D and drink
# options in terms of K notes; one-note feasibility handled by remainder.
best = 0
# A robust standard solution: sort desserts by price and maintain prefix sums;
# drinks consume ceil(B/K) K bills, deserts consume floor(A/K) K bills plus
# remainder ones. If a dessert is paid with one extra K bill, receives change
# K-r in ones, which may violate available X; hence use all K bills then low
# remainder costs. Enumerate drinks count, take cheapest K-note drink costs.
drink = sorted((v + k - 1)//k for v in b)
prefd = [0]
for z in drink: prefd.append(prefd[-1]+z)
dess = sorted(a)
prefa = [0]
for z in dess: prefa.append(prefa[-1]+z)
# For chosen count d desserts, buying at face value requires their total price
# funded by available K notes plus X ones, and enough notes for drinks. For a
# fixed total count maximize via enumerate d and use cheapest prices.
for q in range(min(m,y)+1):
    # q cheapest drinks use q K-notes rounded individually
    needk = prefd[q]
    if needk > y: continue
    rem = y-needk
    # desserts can each use K bills, but aggregate leftover notes and ones.
    lo, hi = 0, min(n, rem + x)
    while lo < hi:
        mid=(lo+hi+1)//2
        # pay cheapest mid desserts with available cash total; K-note cash
        # can be exchanged only through overpayment change, so total-value condition
        if prefa[mid] <= rem*k+x: lo=mid
        else: hi=mid-1
    best=max(best,q+lo)
print(best)
