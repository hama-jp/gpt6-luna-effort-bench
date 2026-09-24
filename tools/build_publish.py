"""Build publish/ from the allowlist in PRECHECK.md §6. Nothing else is copied.

    python3 build_publish.py

Excluded on purpose: raw events.jsonl / session logs / codex_home, archive/,
pilot/, AtCoder problem statements and their sample I/O, editorial-derived
reference solutions, auth files. Paths under the home directory are rewritten
to ~ in every copied text file.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
OUT = EXP / "publish"
HOME = re.compile(r"~")
TEXT = {".py", ".md", ".json", ".txt", ".csv", ".in", ".out", ".cpp", ".toml", ".log"}


def copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix in TEXT or src.name in ("TASK.md",):
        dst.write_text(HOME.sub("~", src.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
    else:
        shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path, skip=lambda p: False):
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if p.is_dir() or skip(rel) or "__pycache__" in rel.parts or ".git" in rel.parts or ".tmp" in rel.parts:
            continue
        copy(p, dst / rel)


def command_summary(events: Path) -> dict:
    cmds = []
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") == "item.completed" and item.get("type") == "command_execution":
            cmds.append({"command": HOME.sub("~", item.get("command", ""))[:500], "exit_code": item.get("exit_code")})
    return {"commands": cmds}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in ("PRECHECK.md", "RESULTS.md", "RESULTS_TABLE.md"):
        copy(EXP / f, OUT / f)
    copy(EXP / "PUBLISH_README.md", OUT / "README.md")
    copy_tree(EXP / "tools", OUT / "tools", skip=lambda r: r.name == "build_publish.py" and False)
    copy_tree(EXP / "sources", OUT / "sources")
    for t in ("t1_feature", "t2_bugfix", "t3_document"):
        copy_tree(EXP / "tasks" / t, OUT / "tasks" / t)
    copy_tree(EXP / "tasks" / "base", OUT / "tasks" / "base")
    copy(EXP / "tasks" / "t4_atcoder" / "TASK.md", OUT / "tasks" / "t4_atcoder" / "TASK.md")
    (OUT / "tasks" / "t4_atcoder" / "problems.md").write_text(
        "# 問題文\n\n問題文は AtCoder の著作物なので同梱していません。原文: "
        "https://atcoder.jp/contests/abc476/tasks (A〜G)。実験では日本語の問題文を "
        "`problems/a.md`〜`g.md` として作業フォルダに置きました。\n", encoding="utf-8")
    for f in ("test_feature_hidden.py", "test_bugfix_hidden.py", "t3_key.py", "t3_key.json"):
        copy(EXP / "hidden" / f, OUT / "hidden" / f)
    copy_tree(EXP / "hidden" / "ref_t1", OUT / "hidden" / "ref_t1")
    copy(EXP / "hidden" / "atcoder" / "make_tests.py", OUT / "hidden" / "atcoder" / "make_tests.py")
    copy_tree(EXP / "hidden" / "atcoder" / "tests", OUT / "hidden" / "atcoder" / "tests",
              skip=lambda r: r.name.startswith("sample"))
    for rec in sorted((EXP / "runs").glob("*/*/r*/record.json")):
        d = rec.parent
        dst = OUT / "runs" / d.relative_to(EXP / "runs")
        for f in ("record.json", "grade.json", "final_message.txt"):
            copy(d / f, dst / f)
        (dst / "commands.json").write_text(json.dumps(command_summary(d / "events.jsonl"), ensure_ascii=False, indent=1),
                                           encoding="utf-8")
        ws = d / "ws"
        copy_tree(ws, dst / "ws", skip=lambda r: r.parts[0] == "problems")
    print("built", OUT)


if __name__ == "__main__":
    main()
