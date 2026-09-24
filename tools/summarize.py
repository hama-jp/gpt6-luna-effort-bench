"""Aggregate runs/ for the two-part design and audit every trial.

    python3 summarize.py [--root runs] [--out RESULTS_TABLE.md]

Audit (a trial is INVALID if any of these happened; listed with the evidence):
* the built-in web search tool was used
* a command touched something outside its own workspace: the experiment
  directory, hidden/answer files, other trials, ~/.codex, $HOME, ~
  other than its workspace, `..` escapes, chmod
Commands that merely *mention* such words are listed as FLAGGED for manual
review (the sandbox + chmod-000 lock is the barrier; the audit is a backstop).

Part 1 = T1–T3 (expected cells: Luna low/medium/high/max × 2)
Part 2 = T4 AtCoder (expected cells: Luna low/medium/high/xhigh/max × 3)
Sol was dropped by the user on 2026-09-24 (see PRECHECK §1).
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
HARD = re.compile(r"gpt6-luna--effort-cost|t3_key|test_\w+_hidden|luna-bench/(?:codexhome|grade)|"
                  r"\.codex|chmod|\$HOME|~/|~/(?!luna-bench/ws/)|(?:^|[\s'\"=])\.\./|/tmp/claude")
SOFT = re.compile(r"hidden|find /|ls /|/proc/|/etc/")
# strings that exist only in the hidden material / this Claude session; seeing one in a
# command's OUTPUT or the agent's messages means something leaked, however the command was written
LEAK = re.compile(r"B6_Cents|R_Regression|F2_RateLookup|F6_ReportAndCli|\"traps\"|FOD = 998244353|"
                  r"\.claude/projects|tool_use_id|t3_key|editorial/\d{5}|ref_t1|make_tests\.py")

EXPECTED = {
    **{(t, "gpt-6-luna", e): 2 for t in ("t1_feature", "t2_bugfix", "t3_document") for e in ("low", "medium", "high", "max")},
    **{("t4_atcoder", "gpt-6-luna", e): 3 for e in ("low", "medium", "high", "xhigh", "max")},
}
ORDER = [("gpt-6-luna", e) for e in ("low", "medium", "high", "xhigh", "max")] + \
        [("gpt-6-sol", e) for e in ("low", "medium", "high", "xhigh", "max")]


def audit(events: Path) -> tuple[list[str], list[str]]:
    hard, soft = [], []
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") != "item.completed":
            continue
        if item.get("type") == "web_search":
            hard.append("WEB_SEARCH: " + str(item.get("query", ""))[:150])
        blob = (item.get("aggregated_output") or "") + (item.get("text") or "")
        m = LEAK.search(blob)
        if m:
            hard.append(f"LEAK in output: {m.group(0)}")
        if item.get("type") == "command_execution":
            cmd = item.get("command", "")
            if HARD.search(cmd):
                hard.append(cmd[:200])
            elif SOFT.search(cmd):
                soft.append(cmd[:200])
    return hard, soft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="runs")
    ap.add_argument("--out")
    a = ap.parse_args()

    cells = defaultdict(list)
    invalid, flagged = [], []
    for rec_path in sorted((EXP / a.root).glob("*/*/r*/record.json")):
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        rec["_dir"] = rec_path.parent
        hard, soft = audit(rec_path.parent / "events.jsonl")
        if soft:
            flagged.append((rec_path.parent, soft))
        if hard:
            invalid.append((rec_path.parent, hard))
            continue
        cells[(rec["task"], rec["model"], rec["effort"])].append(rec)

    L = [f"# 集計({a.root})", ""]
    missing = [(k, n, len(cells.get(k, []))) for k, n in EXPECTED.items() if len(cells.get(k, [])) < n]
    L.append("**揃っていないセル**: " + ("なし" if not missing else
             ", ".join(f"{t}/{m}/{e} {got}/{n}" for (t, m, e), n, got in missing)))
    L.append("")

    # ---- Part 1
    L += ["## 第1部 ふだんの仕事(T1〜T3)", "",
          "| 課題 | モデル | effort | n | 得点(各回) | 平均 % | API換算 $/回 | 秒/回 | 出力トークン/回 |",
          "|---|---|---|---:|---|---:|---:|---:|---:|"]
    for t in ("t1_feature", "t2_bugfix", "t3_document"):
        for m, e in ORDER:
            recs = cells.get((t, m, e))
            if not recs:
                continue
            pct = [100 * r["score"] / r["total"] for r in recs]
            L.append(f"| {t} | {m} | {e} | {len(recs)} | {', '.join(f'{r['score']}/{r['total']}' for r in recs)} | "
                     f"{statistics.mean(pct):.0f} | {statistics.mean(r['api_cost_usd'] for r in recs):.4f}"
                     f"{'' if all(r.get('cost_complete', True) for r in recs) else '(打ち切りあり)'} | "
                     f"{statistics.mean(r['wall_s'] for r in recs):.0f} | "
                     f"{statistics.mean(r['usage'].get('output_tokens', 0) for r in recs):.0f} |")

    # ---- Part 2
    L += ["", "## 第2部 AtCoder ABC476 A〜G(T4)", "",
          "| モデル | effort | n | 正解数(各回) | 平均 | 各回の正解問題 | API換算 $/回 | 分/回 | 1問あたり $ |",
          "|---|---|---:|---|---:|---|---:|---:|---:|"]
    t4 = {}
    for m, e in ORDER:
        recs = cells.get(("t4_atcoder", m, e))
        if not recs:
            continue
        acs = []
        for r in recs:
            g = json.loads((r["_dir"] / "grade.json").read_text(encoding="utf-8"))
            acs.append(g.get("ac", ""))
        mean_ac = statistics.mean(r["score"] for r in recs)
        mean_cost = statistics.mean(r["api_cost_usd"] for r in recs)
        t4[(m, e)] = (mean_ac, mean_cost, recs)
        L.append(f"| {m} | {e} | {len(recs)} | {', '.join(str(r['score']) for r in recs)} | {mean_ac:.2f} | "
                 f"{' / '.join(x or '-' for x in acs)} | {mean_cost:.4f}"
                 f"{'' if all(r.get('cost_complete', True) for r in recs) else '(打ち切りあり)'} | "
                 f"{statistics.mean(r['wall_s'] for r in recs) / 60:.1f} | "
                 f"{(sum(r['api_cost_usd'] for r in recs) / max(1, sum(r['score'] for r in recs))):.4f} |")

    # ---- pre-registered judgements (PRECHECK §1, Part 2)
    L += ["", "## 事前に決めた判定(第2部)", ""]
    lv = [e for e in ("low", "medium", "high", "xhigh", "max") if ("gpt-6-luna", e) in t4]
    if "low" in lv and "max" in lv:
        lo, mx = t4[("gpt-6-luna", "low")], t4[("gpt-6-luna", "max")]
        d = mx[0] - lo[0]
        L.append(f"- effort の効き目: max − low = {d:+.2f} 問 → **{'効く' if d >= 0.5 else '見えない(0.5問未満)'}**")
        enough = next((e for e in lv if mx[0] - t4[("gpt-6-luna", e)][0] <= 0.5), None)
        L.append(f"- 足りる設定(平均正解数が max と 0.5 問以内になる最も低い effort): **{enough}**"
                 + (f"(費用は max の {t4[('gpt-6-luna', enough)][1] / mx[1]:.2f} 倍)" if enough and mx[1] else ""))
        if all(r["score"] == 7 for k in t4 for r in t4[k][2]):
            L.append("- 全セル 7/7 → 課題が易しすぎて何も言えない(反証条件)")
    else:
        L.append("- (セルが揃っていないため判定しない)")

    if invalid:
        L += ["", "## 無効とした試行"]
        L += [f"- {d.relative_to(EXP)}: {bad[0]}" for d, bad in invalid]
    if flagged:
        L += ["", "## 目視確認が要るコマンド(無効にはしていない)"]
        L += [f"- {d.relative_to(EXP)}: {soft[0]}" for d, soft in flagged]
    text = "\n".join(L)
    if a.out:
        (EXP / a.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
