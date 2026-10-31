import io
import json
import sqlite3

import pandas as pd
import pytest

from file_readers import (MAX_FILE_MB, df_to_string, ensure_unique_columns,
                          read_file_to_df)

SAMPLE = pd.DataFrame({"region": ["North", "South", "East"], "revenue": [10, 20, 30]})


def _csv(sep=","):
    return SAMPLE.to_csv(index=False, sep=sep).encode()


def test_csv_and_tsv():
    assert read_file_to_df(_csv(), "a.csv").shape == (3, 2)
    assert read_file_to_df(_csv("\t"), "a.tsv").shape == (3, 2)


def test_json_records_and_dict():
    records = json.dumps(SAMPLE.to_dict("records")).encode()
    assert read_file_to_df(records, "a.json").shape == (3, 2)
    assert read_file_to_df(b'{"a": 1, "b": 2}', "single.json").shape == (1, 2)


def test_xml():
    xml = b"<rows><row><a>1</a><b>x</b></row><row><a>2</a><b>y</b></row></rows>"
    assert read_file_to_df(xml, "a.xml").shape == (2, 2)


def test_excel_parquet_feather_roundtrip():
    buf = io.BytesIO()
    SAMPLE.to_excel(buf, index=False)
    assert read_file_to_df(buf.getvalue(), "a.xlsx").shape == (3, 2)
    buf = io.BytesIO()
    SAMPLE.to_parquet(buf)
    assert read_file_to_df(buf.getvalue(), "a.parquet").shape == (3, 2)
    buf = io.BytesIO()
    SAMPLE.to_feather(buf)
    assert read_file_to_df(buf.getvalue(), "a.feather").shape == (3, 2)


def test_sqlite(tmp_path):
    path = tmp_path / "t.db"
    conn = sqlite3.connect(path)
    SAMPLE.to_sql("sales", conn, index=False)
    conn.close()
    assert read_file_to_df(path.read_bytes(), "t.db").shape == (3, 2)


def test_sqlite_without_tables_is_a_clear_error(tmp_path):
    path = tmp_path / "empty.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE temp_t (x INTEGER)")
    conn.execute("DROP TABLE temp_t")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="No tables"):
        read_file_to_df(path.read_bytes(), "empty.db")


def test_pickle_is_not_supported():
    with pytest.raises(ValueError, match="Unsupported"):
        read_file_to_df(b"anything", "evil.pkl")


def test_empty_and_oversized_files_rejected():
    with pytest.raises(ValueError, match="empty"):
        read_file_to_df(b"", "a.csv")
    with pytest.raises(ValueError, match="larger"):
        read_file_to_df(b"a,b\n" + b"1,2\n" * (MAX_FILE_MB * 1024 * 1024 // 4 + 10), "a.csv")


def test_header_only_csv_rejected():
    with pytest.raises(ValueError, match="No rows"):
        read_file_to_df(b"a,b\n", "a.csv")


def test_duplicate_and_blank_columns_made_unique():
    df = pd.DataFrame([[1, 2, 3]], columns=["a", "a", ""])
    assert list(ensure_unique_columns(df).columns) == ["a", "a_2", "column_3"]


def test_df_to_string_mentions_shape_and_columns():
    text = df_to_string(SAMPLE)
    assert "Shape: 3 rows x 2 columns" in text and "revenue" in text