import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.hard_cases import HARD_DATASETS, HARD_QUESTIONS  # noqa: E402
from benchmark.cases import ground_truth  # noqa: E402
from benchmark.run_hard import strict_match  # noqa: E402


def test_hard_ground_truths_compute():
    frames = {k: v() for k, v in HARD_DATASETS.items()}
    for dataset, _q, fn in HARD_QUESTIONS:
        assert fn is None or ground_truth(fn, frames[dataset]) is not None


def test_hard_tier_shape():
    assert len(HARD_QUESTIONS) == 21
    assert sum(fn is None for _d, _q, fn in HARD_QUESTIONS) == 5


def test_strict_matcher_uses_last_line_only():
    assert strict_match(60.0, "table\n10\n20\nanswer: 60")
    assert not strict_match(60.0, "answer: 60\na\nb\nc")
    assert strict_match("West", "x\nTop region: West")
