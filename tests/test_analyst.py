import pandas as pd

from analyst import MAX_HISTORY_MESSAGES, answer_question, extract_code

DF = pd.DataFrame({"region": ["N", "S", "N", "S"], "revenue": [10, 20, 30, 40]})
GOOD_REPLY = ("ANALYSIS: Sum revenue per region.\n\n```python\n"
              "print(df.groupby('region')['revenue'].sum().to_dict())\n```")


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class FakeClient:
    """Returns scripted replies and records every prompt it receives."""
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs["messages"])
        return _Resp(self.replies.pop(0))


def test_extract_code_variants():
    assert extract_code("x\n```python\nprint(1)\n```") == "print(1)"
    assert extract_code("x\n```\nprint(2)\n```") == "print(2)"
    assert extract_code("no code here") is None


def test_explanation_is_grounded_in_real_output():
    client = FakeClient([GOOD_REPLY, "N total is 40 and S total is 60."])
    result = answer_question(client, "Total revenue by region?", DF, [])
    interpretation_prompt = client.calls[1][-1]["content"]
    assert "{'N': 40, 'S': 60}" in interpretation_prompt          # real output was passed to the model
    assert result["code_output"].strip() == "{'N': 40, 'S': 60}"
    assert "N total is 40" in result["content"] and result["has_code"]


def test_cannot_answer_for_missing_column_runs_no_code():
    client = FakeClient(["CANNOT_ANSWER: there is no salary column; columns are region, revenue."])
    result = answer_question(client, "What is the average salary?", DF, [])
    assert "can't answer" in result["content"] and not result["has_code"]
    assert len(client.calls) == 1


def test_failed_code_gets_one_repair_attempt():
    bad = "ANALYSIS: try.\n\n```python\nprint(df['nope'])\n```"
    client = FakeClient([bad, GOOD_REPLY, "Totals computed."])
    result = answer_question(client, "q", DF, [])
    assert result["code_error"] is None
    assert "{'N': 40, 'S': 60}" in result["code_output"]
    assert len(client.calls) == 3


def test_dangerous_generated_code_is_blocked_end_to_end():
    evil = "ANALYSIS: x\n\n```python\nimport os\nprint(os.environ)\n```"
    client = FakeClient([evil, evil, "The analysis failed."])
    result = answer_question(client, "q", DF, [])
    assert result["code_error"] and "safety check" in result["code_error"]
    assert result["code_output"] == ""


def test_history_is_capped():
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(40)]
    client = FakeClient(["CANNOT_ANSWER: no."])
    answer_question(client, "q", DF, history)
    sent = client.calls[0]                      # system + capped history + question
    assert len(sent) == 1 + MAX_HISTORY_MESSAGES + 1