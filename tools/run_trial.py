"""Run one trial: one task × one model × one effort × one repeat.

    python3 run_trial.py <task> <model> <effort> <rep> [--root runs]

task = t1_feature | t2_bugfix | t3_document | t4_atcoder

Isolation (why each piece exists is in PRECHECK.md §2.5):
* Fresh workspace under WS_ROOT (outside the experiment directory), a git repo
  with one commit. Prompt = TASK.md verbatim, same for every model and effort.
* Fresh CODEX_HOME per trial: only auth.json and a minimal config.toml. No
  history, memories, skills or earlier session logs from the user's ~/.codex.
* codex exec with a Codex permission profile ("bench", extends :workspace):
  write only in the workspace; reads DENIED for ~/.claude (this Claude session's
  transcript and file history hold the hidden material), ~/agents (experiment,
  hidden tests, everything else), Codex history/memory files, /tmp, /var/tmp,
  /dev/shm; TMPDIR points into the workspace (.tmp, git-excluded); no network;
  built-in web search disabled; never asks for approval. No retries, resume or
  extra checks. Timeout per task (T4 100 min, others 60 min).
* While codex runs, the whole experiment directory is chmod 000 so hidden
  tests, answer keys, pilots and earlier trials cannot be read.
* Afterwards: the workspace and the trial's CODEX_HOME session log are moved
  into runs/<task>/<cell>/<rep>/, the solution is graded in a separate sandbox,
  and usage is taken per request from the session log (also for timeouts).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
BENCH = Path("~/luna-bench")
WS_ROOT = BENCH / "ws"
HOME_ROOT = BENCH / "codexhome"
USER_AUTH = Path.home() / ".codex" / "auth.json"
TIMEOUT_MIN = {"t1_feature": 60, "t2_bugfix": 60, "t3_document": 60, "t4_atcoder": 100}

# USD per 1M tokens, developers.openai.com/api/docs/models/<model> (saved in sources/, 2026-09-24).
# cached input = 10% of input, cache write = 1.25x input,
# a request with > 272K input tokens: 2x input/cache rates and 1.5x output for that request.
PRICES = {"gpt-6-luna": (0.10, 0.50), "gpt-6-sol": (2.00, 10.00)}
LONG_PROMPT = 272_000


def request_cost(model: str, u: dict) -> float:
    pin, pout = PRICES[model]
    inp = u.get("input_tokens", 0)
    cached = u.get("cached_input_tokens", 0)
    write = u.get("cache_write_input_tokens", 0)
    fresh = inp - cached - write
    out = u.get("output_tokens", 0)  # includes reasoning tokens
    k_in, k_out = (2.0, 1.5) if inp > LONG_PROMPT else (1.0, 1.0)
    return (fresh * pin + cached * pin * 0.10 + write * pin * 1.25) * k_in / 1e6 + out * pout * k_out / 1e6


def usage_from_rollout(codex_home: Path) -> dict:
    """Per-request usage from the session log (token_count events carry last_token_usage)."""
    reqs, prev_total = [], None
    for f in sorted((codex_home / "sessions").rglob("rollout-*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            p = ev.get("payload") or {}
            if ev.get("type") == "event_msg" and p.get("type") == "token_count":
                info = p.get("info") or {}
                last, total = info.get("last_token_usage"), info.get("total_token_usage")
                if not last or total == prev_total:
                    continue
                prev_total = total
                reqs.append(last)
    return {"requests": reqs, "total": prev_total or {}}


def lock_experiment(locked: bool):
    """chmod 000 on the experiment directory while codex runs (same uid, so this is
    a read barrier, not a security boundary; chmod attempts are flagged by the audit)."""
    os.chmod(EXP, 0 if locked else stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def prepare(task: str, run_id: str) -> tuple[Path, Path]:
    ws, home = WS_ROOT / run_id, HOME_ROOT / run_id
    WS_ROOT.mkdir(parents=True, exist_ok=True)
    HOME_ROOT.mkdir(parents=True, exist_ok=True)
    stale = list(WS_ROOT.iterdir()) + list(HOME_ROOT.iterdir())
    if stale:
        sys.exit(f"leftovers from another trial, move them first: {stale}")
    src = EXP / "tasks" / task
    if task == "t3_document":
        ws.mkdir(parents=True)
        shutil.copy(src / "report.md", ws / "report.md")
    elif task == "t4_atcoder":
        ws.mkdir(parents=True)
        shutil.copytree(src / "problems", ws / "problems")
        (ws / "solutions").mkdir()
        (ws / "solutions" / ".gitkeep").touch()
    else:
        repo = src / "ledgerlite" if (src / "ledgerlite").is_dir() else EXP / "tasks" / "base" / "ledgerlite"
        shutil.copytree(repo, ws, ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ws, check=True)
    subprocess.run(["git", "-c", "user.name=bench", "-c", "user.email=bench@example.com",
                    "commit", "-qm", "initial"], cwd=ws, check=True)
    (ws / ".tmp").mkdir()
    with open(ws / ".git" / "info" / "exclude", "a") as fh:
        fh.write(".tmp/\n")
    home.mkdir(parents=True)
    shutil.copy2(USER_AUTH, home / "auth.json")
    (home / "config.toml").write_text(PROFILE.format(tmpdir=ws / ".tmp"), encoding="utf-8")
    return ws, home


PROFILE = """web_search = "disabled"
default_permissions = "bench"

[permissions.bench]
extends = ":workspace"

[permissions.bench.filesystem]
"~/.claude" = "deny"
"~/agents" = "deny"
"~/.codex/sessions" = "deny"
"~/.codex/archived_sessions" = "deny"
"~/.codex/thread_history_1.sqlite" = "deny"
"~/.codex/thread_history_1.sqlite-wal" = "deny"
"~/.codex/thread_history_1.sqlite-shm" = "deny"
"~/.codex/memories_1.sqlite" = "deny"
"~/.codex/history.jsonl" = "deny"
"~/.codex/session_index.jsonl" = "deny"
"~/.codex/state_5.sqlite" = "deny"
"~/luna-bench/codexhome" = "deny"
"~/luna-bench/grade" = "deny"
"/tmp" = "deny"
"/var/tmp" = "deny"
"/dev/shm" = "deny"
":workspace_roots" = "write"

[permissions.bench.network]
enabled = false

[shell_environment_policy.set]
TMPDIR = "{tmpdir}"
"""


def sync_auth_back(home: Path) -> bool:
    """If codex refreshed the login token inside the trial home, copy it back so the
    user's own ~/.codex keeps a valid token."""
    a = home / "auth.json"
    if a.exists() and a.read_bytes() != USER_AUTH.read_bytes() and a.stat().st_mtime > USER_AUTH.stat().st_mtime:
        shutil.copy2(a, USER_AUTH)
        return True
    return False


def grade(task: str, ws: Path) -> dict:
    if task == "t3_document":
        key = json.loads((EXP / "hidden" / "t3_key.json").read_text(encoding="utf-8"))
        try:
            ans = json.loads((ws / "answers.json").read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {"passed": 0, "total": len(key["key"]), "error": str(exc)}
        if not isinstance(ans, dict):
            return {"passed": 0, "total": len(key["key"]), "error": "answers.json is not an object"}
        detail = {}
        for q, want in key["key"].items():
            raw = ans.get(q)
            got = raw.strip() if isinstance(raw, str) else raw
            # strict: the value must be the string the task asks for (no commas, no numbers)
            detail[q] = {"got": raw, "ok": got == want,
                         "value_ok_ignoring_format": str(got).replace(",", "") == want,
                         "trap": str(got).replace(",", "") == key["traps"].get(q)}
        return {"passed": sum(d["ok"] for d in detail.values()), "total": len(detail),
                "extra_keys": sorted(set(ans) - set(key["key"])), "detail": detail}
    if task == "t4_atcoder":
        tool, args = "grade_atcoder.py", [str(ws)]
    else:
        hidden = EXP / "hidden" / ("test_feature_hidden.py" if task == "t1_feature" else "test_bugfix_hidden.py")
        tool, args = "grade.py", [str(ws), str(hidden)]
    p = subprocess.run([sys.executable, str(EXP / "tools" / tool), *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"grader failed: {p.stderr[-500:]}")
    return json.loads(p.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=list(TIMEOUT_MIN))
    ap.add_argument("model", choices=list(PRICES))
    ap.add_argument("effort")
    ap.add_argument("rep", type=int)
    ap.add_argument("--root", default="runs", help="runs | pilot")
    a = ap.parse_args()

    cell = f"{a.model}-{a.effort}"
    run_id = f"{a.root}-{a.task}-{cell}-r{a.rep}"
    out_dir = EXP / a.root / a.task / cell / f"r{a.rep}"
    if out_dir.exists():
        sys.exit(f"already ran: {out_dir}")
    ws, home = prepare(a.task, run_id)
    prompt = (EXP / "tasks" / a.task / "TASK.md").read_text(encoding="utf-8")
    log_path = BENCH / f"{run_id}.events.jsonl"

    cmd = ["codex", "exec", "--json", "--skip-git-repo-check", "-C", str(ws),
           "-m", a.model, "-c", f"model_reasoning_effort={a.effort}",
           "-c", "approval_policy=never",
           "-c", 'web_search="disabled"', prompt]
    env = dict(os.environ, CODEX_HOME=str(home))
    timeout_s = TIMEOUT_MIN[a.task] * 60
    t0 = time.time()
    lock_experiment(True)
    try:
        with open(log_path, "w") as log:
            try:
                p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.PIPE,
                                   text=True, timeout=timeout_s, env=env, cwd=ws)
                rc, stderr, timed_out = p.returncode, p.stderr, False
            except subprocess.TimeoutExpired as exc:
                err = exc.stderr
                rc, stderr, timed_out = None, err.decode(errors="replace") if isinstance(err, bytes) else (err or ""), True
    finally:
        lock_experiment(False)
    wall = time.time() - t0

    out_dir.mkdir(parents=True)
    shutil.move(str(log_path), str(out_dir / "events.jsonl"))
    (out_dir / "stderr.txt").write_text(stderr or "", encoding="utf-8")
    auth_synced = sync_auth_back(home)

    commands, web_searches, final_msg = 0, 0, ""
    for line in (out_dir / "events.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") != "item.completed":
            continue
        commands += item.get("type") == "command_execution"
        web_searches += item.get("type") == "web_search"
        if item.get("type") == "agent_message":
            final_msg = item.get("text", "")

    usage = usage_from_rollout(home)
    reqs = usage["requests"]
    cost = sum(request_cost(a.model, u) for u in reqs)
    result = grade(a.task, ws)

    shutil.move(str(ws), str(out_dir / "ws"))
    (out_dir / "codex_home").mkdir()
    if (home / "sessions").exists():
        shutil.move(str(home / "sessions"), str(out_dir / "codex_home" / "sessions"))
    (home / "auth.json").unlink()
    shutil.move(str(home), str(out_dir / "codex_home" / "rest"))

    rec = {"task": a.task, "model": a.model, "effort": a.effort, "rep": a.rep,
           "wall_s": round(wall, 1), "returncode": rc, "timed_out": timed_out,
           "requests": len(reqs), "max_request_input": max((u.get("input_tokens", 0) for u in reqs), default=0),
           "long_prompt_requests": sum(u.get("input_tokens", 0) > LONG_PROMPT for u in reqs),
           "commands": commands, "web_searches": web_searches, "usage": usage["total"],
           "api_cost_usd": round(cost, 5), "cost_complete": not timed_out and bool(reqs),
           "score": result.get("passed"), "total": result.get("total"),
           "auth_synced_back": auth_synced,
           "codex_version": subprocess.run(["codex", "--version"], capture_output=True, text=True).stdout.strip(),
           "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t0))}
    (out_dir / "grade.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "record.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "final_message.txt").write_text(final_msg, encoding="utf-8")
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
