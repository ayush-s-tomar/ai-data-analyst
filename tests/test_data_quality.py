import pandas as pd

from file_readers import data_quality


def test_data_quality_counts_problems():
    df = pd.DataFrame({
        "id": [1, 2, 2, 4],
        "amount": ["10", "20", "20", None],
        "name": ["a", "b", "b", "d"],
    })
    report = data_quality(df)
    assert report["rows"] == 4 and report["columns"] == 3
    assert report["duplicate_rows"] == 1
    assert report["missing_cells"] == 1
    assert report["columns_with_missing"] == {"amount": 1}
    assert report["numbers_stored_as_text"] == ["amount"]


def test_data_quality_survives_unhashable_cells():
    df = pd.DataFrame({"x": [[1], [2]]})
    assert data_quality(df)["duplicate_rows"] == 0
