import pandas as pd

from file_readers import clean_numeric_text


def test_text_numbers_are_converted_and_original_is_untouched():
    df = pd.DataFrame({"a": ["1,200", "$300", " 40 ", None, "x"], "b": list("vwxyz")})
    result = clean_numeric_text(df, ["a"])
    assert result["a"].iloc[:3].tolist() == [1200, 300, 40]
    assert result["a"].isna().tolist() == [False, False, False, True, True]
    assert result["b"].tolist() == list("vwxyz")
    assert df["a"].iloc[0] == "1,200"


def test_unknown_columns_are_ignored():
    df = pd.DataFrame({"a": ["1"]})
    assert clean_numeric_text(df, ["missing"]).equals(df)
