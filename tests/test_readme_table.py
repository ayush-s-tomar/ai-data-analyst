import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.readme_table import parse_basic, parse_hard, render_table  # noqa: E402

BASIC = "# Benchmark results\n\n**Overall: 30/30 correct (100%)**\n"
HARD = "**Questions passed on every run: 19/21** | Individual runs passed: 58/63\n"


def test_parsers_read_the_generated_files():
    assert parse_basic(BASIC) == (30, 30)
    assert parse_hard(HARD) == (19, 21, 58, 63)


def test_parsers_return_none_for_missing_text():
    assert parse_basic("") is None and parse_hard("nothing") is None


def test_table_contains_both_tiers():
    table = render_table((30, 30), (19, 21, 58, 63))
    assert "| Basic (30 questions) | 30/30 |" in table
    assert "19/21 questions, 58/63 runs" in table


def test_table_skips_missing_tiers():
    assert "Hard" not in render_table((30, 30), None)
