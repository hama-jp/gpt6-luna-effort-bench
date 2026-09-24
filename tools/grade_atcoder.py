"""Judge a workspace's solutions/<p>.cpp|.py against hidden ABC476 tests.

    python3 grade_atcoder.py <workspace_dir> [--out result.json]

C++: g++ -std=c++20 -O2. Python: the same python3 that runs this script.
Each run is inside bubblewrap (no network, home replaced by an empty tmpfs except
the directory holding the program), stdin = the test input; expected outputs are
never visible to the program. Memory limit via RLIMIT_AS (problem limit).
Each run may go on to 2x the limit so the real time is recorded; a verdict is
TLE when the time exceeds the limit.
Time limit per test = the problem's limit (A–E, G 2 s; F 3 s); Python gets 3x
(CPython here, AtCoder limits assume PyPy). Stack unlimited.
A problem is AC only if every test passes (like AtCoder). If both .cpp and .py
exist, .cpp is judged.
"""
from __future__ import annotations

import argparse
import json
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
TESTS = EXP / "hidden" / "atcoder" / "tests"
TL = dict(a=2, b=2, c=2, d=2, e=2, f=3, g=2)
MEM_MIB = dict(a=1024, b=1024, c=1024, d=1024, e=1024, f=2048, g=1024)
GRADE_ROOT = Path("~/luna-bench/grade")
POINTS = dict(a=100, b=200, c=300, d=425, e=450, f=525, g=625)


def limits(mem_mib: int):
    def f():
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_AS, (mem_mib * 2**20, mem_mib * 2**20))
    return f


def sandboxed(cmd: list[str], box: Path, writable: bool = False) -> list[str]:
    return ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--tmpfs", "~", "--bind" if writable else "--ro-bind", str(box), str(box), "--tmpfs", "/tmp",
            "--unshare-net", "--die-with-parent", "--chdir", str(box), *cmd]


def judge_problem(p: str, sol_dir: Path, tmp: Path) -> dict:
    cpp, py = sol_dir / f"{p}.cpp", sol_dir / f"{p}.py"
    if cpp.exists():
        exe = tmp / p
        shutil.copy(cpp, tmp / f"{p}.cpp")
        # compile inside the sandbox too: an #include of an absolute path could
        # otherwise pull expected outputs into the binary at compile time
        c = subprocess.run(sandboxed(["g++", "-std=c++20", "-O2", "-o", str(exe), str(tmp / f"{p}.cpp")], tmp, writable=True),
                           capture_output=True, text=True, timeout=120)
        if c.returncode != 0:
            return {"lang": "cpp", "verdict": "CE", "passed": 0, "total": 0, "detail": c.stderr[-300:]}
        cmd, lang = [str(exe)], "cpp"
    elif py.exists():
        shutil.copy(py, tmp / f"{p}.py")
        cmd, lang = [sys.executable, str(tmp / f"{p}.py")], "py"
    else:
        return {"lang": None, "verdict": "NO_SUBMISSION", "passed": 0, "total": 0}
    limit = TL[p] * (3 if lang == "py" else 1)
    cases = sorted((TESTS / p).glob("*.in"))
    passed, worst, first_fail = 0, 0.0, None
    for case in cases:
        exp = case.with_suffix(".out").read_text().split()
        t0 = time.time()
        try:
            with case.open() as fin:
                r = subprocess.run(sandboxed(cmd, tmp), stdin=fin, capture_output=True, text=True,
                                   timeout=2 * limit, preexec_fn=limits(MEM_MIB[p]))
            dt = time.time() - t0
            if dt > limit:
                verdict = "TLE"
            else:
                verdict = "AC" if r.returncode == 0 and r.stdout.split() == exp else ("RE" if r.returncode != 0 else "WA")
        except subprocess.TimeoutExpired:
            dt, verdict = 2 * limit, "TLE(>2x)"
        worst = max(worst, dt)
        if verdict == "AC":
            passed += 1
        elif first_fail is None:
            first_fail = f"{case.stem}: {verdict}"
    return {"lang": lang, "verdict": "AC" if passed == len(cases) else first_fail,
            "passed": passed, "total": len(cases), "max_time_s": round(worst, 2)}


def grade(ws: Path) -> dict:
    res = {}
    GRADE_ROOT.mkdir(parents=True, exist_ok=True)
    for p in "abcdefg":
        with tempfile.TemporaryDirectory(dir=GRADE_ROOT) as tmp:
            res[p] = judge_problem(p, ws / "solutions", Path(tmp))
    ac = [p for p, r in res.items() if r["verdict"] == "AC"]
    return {"problems": res, "passed": len(ac), "total": 7,
            "points": sum(POINTS[p] for p in ac), "ac": "".join(ac).upper()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = grade(Path(a.workspace))
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
