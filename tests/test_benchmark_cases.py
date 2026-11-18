import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.cases import DATASETS, QUESTIONS, ground_truth, matches  # noqa: E402


def test_every_ground_truth_computes():
    frames = {name: build() for name, build in DATASETS.items()}
    for dataset, _question, fn in QUESTIONS:
        value = ground_truth(fn, frames[dataset])
        assert fn is None or value is not None


def test_benchmark_has_thirty_questions_with_refusals():
    assert len(QUESTIONS) == 30
    assert sum(fn is None for _d, _q, fn in QUESTIONS) == 3


def test_matcher_numbers_and_labels():
    assert matches(1234.5, "total: 1,234.5")
    assert matches(100.0, "value 100.4")
    assert not matches(100.0, "value 120")
    assert matches("West", "the top region is west")
    assert not matches("West", "North")
