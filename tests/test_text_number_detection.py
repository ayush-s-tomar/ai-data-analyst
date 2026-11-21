import pandas as pd

from file_readers import clean_numeric_text, data_quality


def test_comma_and_currency_text_is_detected():
    df = pd.DataFrame({"amount": ["1,200", "$300", "40", None], "name": ["a", "b", "c", "d"]})
    assert data_quality(df)["numbers_stored_as_text"] == ["amount"]


def test_detected_columns_can_be_converted():
    df = pd.DataFrame({"amount": ["1,200", "$300", "40"]})
    flagged = data_quality(df)["numbers_stored_as_text"]
    assert clean_numeric_text(df, flagged)["amount"].tolist() == [1200, 300, 40]


def test_ordinary_text_is_not_flagged():
    df = pd.DataFrame({"city": ["Pune", "Delhi", "Agra"]})
    assert data_quality(df)["numbers_stored_as_text"] == []
