import pandas as pd

from file_readers import numeric_profile


def test_profile_has_one_row_per_numeric_column():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [10.0, 20.0, 30.0], "c": list("xyz")})
    profile = numeric_profile(df)
    assert list(profile.index) == ["a", "b"]
    assert profile.loc["a", "mean"] == 2 and profile.loc["b", "max"] == 30


def test_profile_is_empty_without_numeric_columns():
    assert numeric_profile(pd.DataFrame({"c": ["x", "y"]})).empty
