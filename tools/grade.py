"""Grade one workspace against a hidden test file, per test class.

    python3 grade.py <workspace_dir> <hidden_test.py> [--out result.json]

The workspace's ``ledgerlite`` package is copied into a fresh temp dir together
with the hidden test file, so nothing the agent wrote into its own tests/
directory is used. Each test class is run in a separate subprocess with a
timeout, inside bubblewrap: no network, the home directory replaced by an
empty tmpfs except the temp dir, so the submitted code cannot read other
hidden tests, answer keys or earlier trials. (It can still see the one test
module that is importing it; that is inherent to unit testing.)
A class counts as passed only if all its tests pass.
"""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def classes_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.ClassDef)]


GRADE_ROOT = Path("~/luna-bench/grade")


def sandboxed(cmd: list[str], tmp: Path) -> list[str]:
    return ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--tmpfs", "~", "--bind", str(tmp), str(tmp), "--tmpfs", "/tmp",
            "--unshare-net", "--die-with-parent", "--chdir", str(tmp), *cmd]


def grade(workspace: Path, hidden: Path) -> dict:
    results = {}
    GRADE_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=GRADE_ROOT) as tmp:
        tmp = Path(tmp)
        pkg = workspace / "ledgerlite"
        if not pkg.is_dir():
            return {"error": f"no package at {pkg}", "classes": {}}
        shutil.copytree(pkg, tmp / "ledgerlite", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(hidden, tmp / "hidden_test.py")
        for cls in classes_in(hidden):
            try:
                p = subprocess.run(sandboxed([sys.executable, "-m", "unittest", f"hidden_test.{cls}"], tmp),
                                   cwd=tmp, capture_output=True, text=True, timeout=60)
                ok = p.returncode == 0
                tail = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""
            except subprocess.TimeoutExpired:
                ok, tail = False, "TIMEOUT"
            results[cls] = {"pass": ok, "last_line": tail}
    return {"classes": results,
            "passed": sum(r["pass"] for r in results.values()),
            "total": len(results)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("hidden")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = grade(Path(a.workspace), Path(a.hidden))
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
