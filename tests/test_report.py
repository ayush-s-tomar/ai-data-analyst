from report import build_report


def test_report_contains_questions_answers_and_output():
    messages = [
        {"role": "assistant", "content": "Summary", "is_initial": True},
        {"role": "user", "content": "Total revenue?"},
        {"role": "assistant", "content": "It is 60.", "code_output": "60\n", "charts": [b"png"]},
    ]
    text = build_report("sales.csv", messages)
    assert text.startswith("# Analysis report: sales.csv")
    assert "## Question: Total revenue?" in text and "It is 60." in text
    assert "```text\n60\n```" in text and "1 chart(s)" in text


def test_report_handles_no_messages():
    assert build_report("x.csv", []).strip() == "# Analysis report: x.csv"
