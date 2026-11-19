import pandas as pd

from file_readers import df_to_string, sensitive_columns


def test_sensitive_columns_match_whole_words_only():
    df = pd.DataFrame(columns=["Email", "phone_number", "company", "pan_card", "revenue"])
    assert sensitive_columns(df) == ["Email", "phone_number", "pan_card"]


def test_hidden_values_never_reach_the_prompt():
    df = pd.DataFrame({"email": ["secret@example.com"] * 3, "sales": [1, 2, 3]})
    text = df_to_string(df, hidden=["email"])
    assert "secret@example.com" not in text and "<hidden>" in text and "email" in text


def test_no_hidden_columns_leaves_values_visible():
    df = pd.DataFrame({"email": ["a@b.com"], "sales": [1]})
    assert "a@b.com" in df_to_string(df)
