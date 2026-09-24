"""Run the whole main grid (39 trials, Luna only) one at a time, cells interleaved.

    python3 run_all.py [--dry-run]

Order: round-robin over cells, so time of day and server load are spread over
all cells, and a quota problem on Sol shows up early instead of at the end.
Trials that already have runs/<task>/<cell>/r<n>/record.json are skipped, so
the script can be restarted.

Stop rule (PRECHECK §3): if a trial ends with a non-zero exit and zero model
requests, or its stderr mentions a usage/rate limit, stop the whole run and
report. Do not swap in other cells.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
PLAN = (
    [("t1_feature", m, e, 2) for m, e in [("gpt-6-luna", "low"), ("gpt-6-luna", "medium"), ("gpt-6-luna", "high"), ("gpt-6-luna", "max")]]
    + [("t2_bugfix", m, e, 2) for m, e in [("gpt-6-luna", "low"), ("gpt-6-luna", "medium"), ("gpt-6-luna", "high"), ("gpt-6-luna", "max")]]
    + [("t3_document", m, e, 2) for m, e in [("gpt-6-luna", "low"), ("gpt-6-luna", "medium"), ("gpt-6-luna", "high"), ("gpt-6-luna", "max")]]
    + [("t4_atcoder", "gpt-6-luna", e, 3) for e in ("low", "medium", "high", "xhigh", "max")]
)
LIMIT = re.compile(r"usage limit|rate limit|quota|429|Too Many Requests", re.I)


def schedule() -> list[tuple[str, str, str, int]]:
    """Round 1 = rep 1 of every cell, round 2 = rep 2, ... (interleaved)."""
    out = []
    for rep in range(1, 4):
        for task, model, effort, n in PLAN:
            if rep <= n:
                out.append((task, model, effort, rep))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    todo = schedule()
    print(f"{len(todo)} trials planned")
    for i, (task, model, effort, rep) in enumerate(todo, 1):
        rec = EXP / "runs" / task / f"{model}-{effort}" / f"r{rep}" / "record.json"
        if rec.exists():
            continue
        print(f"[{i}/{len(todo)}] {task} {model} {effort} r{rep}", flush=True)
        if a.dry_run:
            continue
        p = subprocess.run([sys.executable, str(EXP / "tools" / "run_trial.py"), task, model, effort, str(rep)],
                           capture_output=True, text=True)
        if p.returncode != 0:
            print(f"STOP: run_trial failed: {p.stderr[-800:]}", flush=True)
            sys.exit(1)
        r = json.loads(p.stdout.strip().splitlines()[-1])
        stderr = (rec.parent / "stderr.txt").read_text(encoding="utf-8", errors="replace")
        print(f"    score {r['score']}/{r['total']}  {r['wall_s']:.0f}s  ${r['api_cost_usd']:.4f}  "
              f"req {r['requests']}  web {r['web_searches']}  timeout {r['timed_out']}", flush=True)
        if (r["returncode"] not in (0, None) and r["requests"] == 0) or LIMIT.search(stderr):
            print(f"STOP: looks like a quota/limit problem. stderr tail: {stderr[-500:]}", flush=True)
            sys.exit(2)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
