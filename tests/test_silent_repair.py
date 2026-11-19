import pandas as pd

from analyst import answer_question

DF = pd.DataFrame({"region": ["N", "S"], "revenue": [10, 20]})
SILENT = "ANALYSIS: compute.\n\n```python\ntotal = df['revenue'].sum()\n```"
LOUD = "ANALYSIS: compute.\n\n```python\nprint(df['revenue'].sum())\n```"


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
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs["messages"])
        return _Resp(self.replies.pop(0))


def test_silent_code_gets_a_repair_attempt():
    client = FakeClient([SILENT, LOUD, "Total is 30."])
    result = answer_question(client, "Total revenue?", DF, [])
    assert "30" in result["code_output"]
    assert len(client.calls) == 3
    assert "printed nothing" in client.calls[1][-1]["content"]


def test_code_with_output_is_not_repaired():
    client = FakeClient([LOUD, "Total is 30."])
    answer_question(client, "Total revenue?", DF, [])
    assert len(client.calls) == 2
