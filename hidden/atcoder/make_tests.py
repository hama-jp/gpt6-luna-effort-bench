"""Build hidden test cases for ABC476 A–G.

For every problem: the official samples, random small cases whose expected
output comes from the reference AND is cross-checked against an independent
brute force (any disagreement aborts), and max-size cases (reference only).

    python3 make_tests.py            # writes tests/<p>/<name>.in / .out
"""
from __future__ import annotations

import random
import re
import resource
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE / "ref"
OUT = HERE / "tests"
STATEMENTS = HERE.parent.parent / "tasks" / "t4_atcoder" / "problems"
rng = random.Random(476)


def unlimited_stack():
    resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))


def run_ref(p: str, inp: str) -> str:
    exe = [str(REF / p)] if (REF / p).exists() else [sys.executable, str(REF / f"{p}.py")]
    r = subprocess.run(exe, input=inp, capture_output=True, text=True, timeout=120, preexec_fn=unlimited_stack)
    if r.returncode != 0:
        raise RuntimeError(f"ref {p} failed: {r.stderr[:300]}")
    return r.stdout


def norm(s: str) -> list[str]:
    return s.split()


# ---------------- brute forces (independent of the references) ----------------

def brute_a(inp):
    s = inp.split()[0]
    return s + ("r" if s[-1] == "e" else "er")


def brute_b(inp):
    _, s, t = inp.split()
    ok = all(t[i] in ("*", s[i]) for i in range(len(s)))
    return "Yes" if ok else "No"


def brute_c(inp):
    d = list(map(int, inp.split()))
    a = d[1:]
    return "\n".join(str(sorted(a[:k], reverse=True)[2]) for k in range(3, len(a) + 1))


def brute_d(inp):
    d = list(map(int, inp.split()))
    n, m, k, x, y = d[:5]
    a = d[5:5 + n]
    b = d[5 + n:5 + n + m]

    @lru_cache(maxsize=None)
    def best(ones, kb, bought):
        res = 0
        for i in range(n):
            if bought >> i & 1:
                continue
            for t in range(0, kb + 1):
                need = max(0, a[i] - t * k)
                if need > ones:
                    continue
                change = max(0, t * k - a[i])
                res = max(res, 1 + best(ones - need + change, kb - t, bought | 1 << i))
                if t * k >= a[i]:
                    break
        for j in range(m):
            if bought >> (n + j) & 1:
                continue
            for t in range(-(-b[j] // k), kb + 1):
                res = max(res, 1 + best(ones + t * k - b[j], kb - t, bought | 1 << (n + j)))
        return res

    return str(best(x, y, 0))


def brute_e(inp):
    d = list(map(int, inp.split()))
    n, m = d[:2]
    p = d[2:2 + n]
    q = d[2 + n:]
    for i in range(m):
        l, r = q[2 * i] - 1, q[2 * i + 1]
        seg = p[l:r]
        i1 = l + seg.index(min(seg))
        i2 = l + seg.index(max(seg))
        p[i1], p[i2] = p[i2], p[i1]
    return " ".join(map(str, p))


def brute_f(inp):
    d = list(map(int, inp.split()))
    n, mod = d[:2]
    a = d[2:2 + n]
    b = d[2 + n:2 + 2 * n]
    c = [[a[i] * b[j] % mod for j in range(n)] for i in range(n)]
    ans = 0
    for ti in range(n):
        for tj in range(n):
            f = sum(c[i][j] * max(abs(i - ti), abs(j - tj)) for i in range(n) for j in range(n))
            ans ^= f + ti * n + tj
    return str(ans)


def brute_g(inp):
    d = list(map(int, inp.split()))
    out = []
    for i in range(d[0]):
        l, r = d[1 + 2 * i], d[2 + 2 * i]
        pc = [bin(v).count("1") for v in range(l, r + 1)]
        # min number of chains (strictly increasing popcount) = longest non-increasing subsequence
        best = [1] * len(pc)
        for j in range(len(pc)):
            for i2 in range(j):
                if pc[i2] >= pc[j]:
                    best[j] = max(best[j], best[i2] + 1)
        out.append(str(max(best)))
    return "\n".join(out)


BRUTE = dict(a=brute_a, b=brute_b, c=brute_c, d=brute_d, e=brute_e, f=brute_f, g=brute_g)


# ---------------- generators ----------------

def g_a(small):
    n = rng.randint(1, 10)
    s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n - 1)) + rng.choice("eeexyz")
    return s + "\n"


def g_b(small):
    n = rng.randint(1, 100 if not small else 8)
    s = "".join(rng.choice("ab") for _ in range(n))
    t = "".join("*" if rng.random() < 0.4 else (c if rng.random() < 0.9 else rng.choice("ab")) for c in s)
    return f"{n}\n{s}\n{t}\n"


def g_c(small):
    n = rng.randint(3, 12) if small else 500000
    hi = rng.choice([3, 10, 10**9]) if small else rng.choice([5, 10**9])
    a = [rng.randint(1, hi) for _ in range(n)]
    if not small and rng.random() < 0.5:
        a.sort()
    return f"{n}\n{' '.join(map(str, a))}\n"


def g_d(small):
    if small:
        n, m = rng.randint(1, 3), rng.randint(1, 3)
        k = rng.randint(2, 5)
        x, y = rng.randint(0, 12), rng.randint(0, 5)
        a = [rng.randint(1, 12) for _ in range(n)]
        b = [rng.randint(1, 12) for _ in range(m)]
    else:
        n = m = 200000
        k = rng.choice([2, 1000, 10**9])
        x = rng.randint(0, 10**15)
        y = rng.randint(0, 10**9)
        a = [rng.randint(1, 10**9) for _ in range(n)]
        b = [rng.randint(1, 10**9) for _ in range(m)]
    return f"{n} {m} {k}\n{x} {y}\n{' '.join(map(str, a))}\n{' '.join(map(str, b))}\n"


def g_e(small):
    n = rng.randint(2, 8) if small else 200000
    m = rng.randint(1, 10) if small else 200000
    p = list(range(1, n + 1))
    rng.shuffle(p)
    qs = []
    for _ in range(m):
        if not small and rng.random() < 0.5:
            l, r = 1, n
        else:
            l = rng.randint(1, n - 1)
            r = rng.randint(l + 1, n)
        qs.append(f"{l} {r}")
    return f"{n} {m}\n{' '.join(map(str, p))}\n" + "\n".join(qs) + "\n"


def g_f(small):
    n = rng.randint(1, 6) if small else 1500
    mod = rng.randint(2, 30) if small else rng.choice([2 * 10**6, 1999993])
    a = [rng.randint(1, mod - 1) for _ in range(n)]
    b = [rng.randint(1, mod - 1) for _ in range(n)]
    return f"{n} {mod}\n{' '.join(map(str, a))}\n{' '.join(map(str, b))}\n"


def g_g(small):
    t = rng.randint(1, 5) if small else 10000
    cases = []
    for _ in range(t):
        if small:
            l = rng.randint(1, 300)
            r = rng.randint(l, min(l + rng.choice([0, 5, 60, 400]), 700))
        else:
            e = rng.randint(1, 60)
            l = rng.randint(1, min(10**18, 2**e))
            r = rng.randint(l, min(10**18, l + rng.choice([0, 10, 2**e, 10**18])))
        cases.append(f"{l} {r}")
    return f"{t}\n" + "\n".join(cases) + "\n"


GEN = dict(a=g_a, b=g_b, c=g_c, d=g_d, e=g_e, f=g_f, g=g_g)
N_SMALL = dict(a=10, b=15, c=20, d=40, e=30, f=20, g=40)
N_LARGE = dict(a=0, b=3, c=3, d=4, e=3, f=2, g=3)


def samples(p: str) -> list[tuple[str, str]]:
    md = (STATEMENTS / f"{p}.md").read_text(encoding="utf-8")
    ins = re.findall(r"### 入力例 \d+\s*```\n(.*?)```", md, re.S)
    outs = re.findall(r"### 出力例 \d+\s*```\n(.*?)```", md, re.S)
    return list(zip(ins, outs))


def main():
    for p in "abcdefg":
        d = OUT / p
        d.mkdir(parents=True, exist_ok=True)
        cases = []
        for i, (inp, exp) in enumerate(samples(p), 1):
            got = run_ref(p, inp)
            assert norm(got) == norm(exp), f"ref {p} fails sample {i}"
            cases.append((f"sample{i}", inp, exp))
        for i in range(N_SMALL[p]):
            inp = GEN[p](True)
            got = run_ref(p, inp)
            want = BRUTE[p](inp)
            assert norm(got) == norm(want), f"ref/brute disagree on {p} small{i}:\n{inp}\nref={got}\nbrute={want}"
            cases.append((f"small{i:02d}", inp, got))
        for i in range(N_LARGE[p]):
            inp = GEN[p](False)
            cases.append((f"large{i}", inp, run_ref(p, inp)))
        for name, inp, exp in cases:
            (d / f"{name}.in").write_text(inp)
            (d / f"{name}.out").write_text(exp if exp.endswith("\n") else exp + "\n")
        print(p, len(cases), "cases OK")


if __name__ == "__main__":
    main()
