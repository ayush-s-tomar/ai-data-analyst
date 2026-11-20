import ast

from scriptexport import build_script

MESSAGES = [
    {"role": "assistant", "content": "Summary", "is_initial": True},
    {"role": "user", "content": "Total revenue\nby region?"},
    {"role": "assistant", "content": "**Analysis:** sum\n\n```python\nprint(df.groupby('region')['revenue'].sum())\n```\n\n**Interpretation:** ok"},
]


def test_script_contains_code_with_its_question():
    text = build_script("sales.csv", MESSAGES)
    assert "# Question: Total revenue by region?" in text
    assert "print(df.groupby('region')['revenue'].sum())" in text
    assert "'sales.csv'" in text


def test_script_is_valid_python():
    ast.parse(build_script("sales.csv", MESSAGES))


def test_script_without_code_is_still_valid():
    ast.parse(build_script("x.csv", []))
