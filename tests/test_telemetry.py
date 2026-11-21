import logging

import pytest

from telemetry import timed_answer


def test_success_is_logged_without_content(caplog):
    caplog.set_level(logging.INFO, logger="ada")
    result = {"has_code": True, "code_error": None, "charts": [b"x"], "content": "SECRET ANSWER"}
    assert timed_answer(lambda question: result, "SECRET QUESTION") is result
    text = caplog.text
    assert "has_code=True" in text and "charts=1" in text
    assert "SECRET" not in text


def test_failure_is_logged_by_type_and_reraised(caplog):
    caplog.set_level(logging.WARNING, logger="ada")

    def boom():
        raise ValueError("private detail")

    with pytest.raises(ValueError):
        timed_answer(boom)
    assert "ValueError" in caplog.text and "private detail" not in caplog.text
