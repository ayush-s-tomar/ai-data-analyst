"""Accuracy benchmark: run known-answer questions through the real pipeline.

Usage (from the repo root):
  python -m benchmark.run_benchmark --dry-run       # check ground truth only, no API calls
  python -m benchmark.run_benchmark                 # full run (needs GROQ_API_KEY)
  python -m benchmark.run_benchmark --limit 5       # quick smoke test

A question passes when the number or label the CODE printed matches the pandas ground truth.
Questions the data cannot answer pass only if the model refuses instead of running code.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "streamlit_app"))

from benchmark.cases import DATASETS, QUESTIONS, ground_truth, matches  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent


def load_key():
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    secrets = ROOT / "streamlit_app" / ".streamlit" / "secrets.toml"
    if secrets.exists():
        for line in secrets.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith("GROQ_API_KEY"):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


def dry_run():
    frames = {name: build() for name, build in DATASETS.items()}
    for dataset, question, fn in QUESTIONS:
        print(f"[{dataset}] {question} -> {ground_truth(fn, frames[dataset])}")
    print(f"\nOK: {len(QUESTIONS)} questions, ground truth computed for all.")


def run_live(limit, delay):
    import groq
    from analyst import GROQ_MODEL, LLMError, answer_question

    key = load_key()
    if not key:
        sys.exit("Set GROQ_API_KEY (env var) or add it to streamlit_app/.streamlit/secrets.toml")
    client = groq.Groq(api_key=key)
    frames = {name: build() for name, build in DATASETS.items()}
    rows = []
    for dataset, question, fn in QUESTIONS[:limit]:
        df = frames[dataset]
        expected = ground_truth(fn, df)
        result, error = None, ""
        for _ in range(2):
            try:
                result = answer_question(client, question, df, [])
                break
            except LLMError as exc:
                error = str(exc)
                time.sleep(30)
        if result is None:
            status, note = "error", error
        elif expected is None:
            status = "pass" if not result["has_code"] else "fail"
            note = "refused" if status == "pass" else "ran code instead of refusing"
        else:
            ok = result["has_code"] and not result["code_error"] and matches(expected, result["code_output"])
            status = "pass" if ok else "fail"
            note = "" if ok else (result["code_error"] or result["code_output"] or "no output")[:120].replace("\n", " ")
        rows.append({"dataset": dataset, "question": question, "expected": expected, "status": status, "note": note})
        print(f"{status.upper():5} [{dataset}] {question}")
        time.sleep(delay)

    write_report(rows, GROQ_MODEL)


def write_report(rows, model):
    scored = [r for r in rows if r["status"] != "error"]
    passed = sum(r["status"] == "pass" for r in scored)
    stamp = datetime.date.today().isoformat()
    lines = [
        "# Benchmark results", "",
        f"Model: `{model}` | Date: {stamp} | Questions scored: {len(scored)} of {len(rows)}", "",
        f"**Overall: {passed}/{len(scored)} correct ({100 * passed / max(len(scored), 1):.0f}%)**", "",
        "| Dataset | Passed | Total |", "|---|---|---|",
    ]
    for name in DATASETS:
        subset = [r for r in scored if r["dataset"] == name]
        lines.append(f"| {name} | {sum(r['status'] == 'pass' for r in subset)} | {len(subset)} |")
    failures = [r for r in rows if r["status"] != "pass"]
    if failures:
        lines += ["", "## Failures and errors", "", "| Dataset | Question | Expected | Status | Note |", "|---|---|---|---|---|"]
        for r in failures:
            lines.append(f"| {r['dataset']} | {r['question']} | {r['expected']} | {r['status']} | {r['note']} |")
    (OUT_DIR / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"\nOverall: {passed}/{len(scored)}. Wrote benchmark/results.md and results.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=len(QUESTIONS))
    parser.add_argument("--delay", type=float, default=2.0, help="seconds between questions")
    args = parser.parse_args()
    if args.dry_run:
        dry_run()
    else:
        run_live(args.limit, args.delay)


if __name__ == "__main__":
    main()
