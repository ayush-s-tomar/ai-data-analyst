import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.hard_cases import HARD_QUESTIONS  # noqa: E402
from benchmark.run_hard import select_questions  # noqa: E402


def test_only_filters_by_question_text_case_insensitively():
    chosen = select_questions(HARD_QUESTIONS, "LAST YEAR")
    assert len(chosen) == 1 and "last year" in chosen[0][1]


def test_limit_caps_the_selection():
    assert len(select_questions(HARD_QUESTIONS, "", 3)) == 3


def test_no_filter_returns_everything():
    assert len(select_questions(HARD_QUESTIONS)) == len(HARD_QUESTIONS)
