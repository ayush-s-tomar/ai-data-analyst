import pandas as pd

from file_readers import df_to_string


def test_long_text_cells_are_truncated_in_the_prompt():
    df = pd.DataFrame({"note": ["x" * 500] * 5, "n": range(5)})
    text = df_to_string(df)
    assert "x" * 100 not in text and "..." in text


def test_wide_frames_keep_the_column_list():
    df = pd.DataFrame({f"col_{i}": range(3) for i in range(120)})
    text = df_to_string(df)
    assert "col_119" in text
