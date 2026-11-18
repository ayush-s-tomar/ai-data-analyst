"""Harder benchmark: python -m benchmark.run_hard [--runs 3] [--delay 4] [--limit N] [--dry-run].

Strict check: a number must appear in the LAST printed line (or the label anywhere in the last line).
Each question is run --runs times; it counts as passed only if EVERY run passes.
Note: this metric is harsher than the basic tier on purpose.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "streamlit_app"))

from benchmark.cases import ground_truth, numbers_in  # noqa: E402
from benchmark.hard_cases import HARD_DATASETS, HARD_QUESTIONS  # noqa: E402
from benchmark.run_benchmark import load_key  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent


def last_line(text):
    lines = [x for x in (text or "").strip().splitlines() if x.strip()]
    return lines[-1] if lines else ""


def strict_match(expected, output):
    """Labels: found anywhere in the output. Numbers: found in the last 3 non-empty lines."""
    if isinstance(expected, str):
        return expected.lower() in (output or "").lower()
    lines = [x for x in (output or "").strip().splitlines() if x.strip()]
    tail = "\n".join(lines[-3:])
    return any(math.isclose(n, expected, rel_tol=0.01, abs_tol=0.01) for n in numbers_in(tail))


def judge(expected, result):
    if result is None:
        return "error", "no result"
    if expected is None:
        return ("pass", "refused") if not result["has_code"] else ("fail", "ran code instead of refusing")
    if not result["has_code"] or result["code_error"]:
        return "fail", (result["code_error"] or "no code")[:120].replace("\n", " ")
    if strict_match(expected, result["code_output"]):
        return "pass", ""
    return "fail", ("last line: " + last_line(result["code_output"]))[:120]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--limit", type=int, default=len(HARD_QUESTIONS))
    args = parser.parse_args()

    frames = {k: v() for k, v in HARD_DATASETS.items()}
    if args.dry_run:
        for dataset, question, fn in HARD_QUESTIONS:
            print(f"[{dataset}] {question} -> {ground_truth(fn, frames[dataset])}")
        print(f"\nOK: {len(HARD_QUESTIONS)} hard questions.")
        return

    import groq
    from analyst import GROQ_MODEL, LLMError, answer_question

    key = load_key()
    if not key:
        sys.exit("Set GROQ_API_KEY or add it to streamlit_app/.streamlit/secrets.toml")
    client = groq.Groq(api_key=key)

    rows = []
    for dataset, question, fn in HARD_QUESTIONS[:args.limit]:
        expected = ground_truth(fn, frames[dataset])
        verdicts = []
        for _ in range(args.runs):
            result = None
            for _try in range(2):
                try:
                    result = answer_question(client, question, frames[dataset], [])
                    break
                except LLMError:
                    time.sleep(30)
            verdicts.append(judge(expected, result))
            time.sleep(args.delay)
        passes = sum(v[0] == "pass" for v in verdicts)
        status = "pass" if passes == len(verdicts) else "fail"
        note = next((v[1] for v in verdicts if v[0] != "pass"), "")
        rows.append({"dataset": dataset, "question": question, "expected": expected,
                     "status": status, "runs_passed": f"{passes}/{len(verdicts)}", "note": note})
        print(f"{status.upper():5} {passes}/{len(verdicts)} [{dataset}] {question}")

    total = len(rows)
    ok = sum(r["status"] == "pass" for r in rows)
    consistent_runs = sum(int(r["runs_passed"].split("/")[0]) for r in rows)
    all_runs = sum(int(r["runs_passed"].split("/")[1]) for r in rows)
    lines = ["# Hard benchmark results", "",
             f"Model: `{GROQ_MODEL}` | Date: {datetime.date.today().isoformat()} | Runs per question: {args.runs}", "",
             f"**Questions passed on every run: {ok}/{total}** | Individual runs passed: {consistent_runs}/{all_runs}", "",
             "| Dataset | Question | Runs passed | Note |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['dataset']} | {r['question']} | {r['runs_passed']} | {r['note']} |")
    (OUT_DIR / "results_hard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "results_hard.json").write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"\nPassed on every run: {ok}/{total}. Wrote benchmark/results_hard.md")


if __name__ == "__main__":
    main()
