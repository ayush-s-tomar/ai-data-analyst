"""Build the README benchmark table from results.md and results_hard.md.

Usage: python -m benchmark.readme_table
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def parse_basic(text: str):
    match = re.search(r"Overall: (\d+)/(\d+)", text or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def parse_hard(text: str):
    match = re.search(r"every run: (\d+)/(\d+)\*\* \| Individual runs passed: (\d+)/(\d+)", text or "")
    return tuple(int(x) for x in match.groups()) if match else None


def render_table(basic, hard) -> str:
    rows = ["| Tier | Result |", "|---|---|"]
    if basic:
        rows.append(f"| Basic ({basic[1]} questions) | {basic[0]}/{basic[1]} |")
    if hard:
        rows.append(f"| Hard ({hard[1]} questions, repeated runs) | {hard[0]}/{hard[1]} questions, {hard[2]}/{hard[3]} runs |")
    return "\n".join(rows) + "\n"


def main() -> None:
    def read(name):
        path = HERE / name
        return path.read_text(encoding="utf-8") if path.exists() else ""

    print(render_table(parse_basic(read("results.md")), parse_hard(read("results_hard.md"))))


if __name__ == "__main__":
    main()
