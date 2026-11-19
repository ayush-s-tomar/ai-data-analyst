import io
import sqlite3

import pandas as pd
import pytest

from file_readers import list_sources, read_file_to_df


def _two_sheet_xlsx():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as writer:
        pd.DataFrame({"a": [1, 2]}).to_excel(writer, sheet_name="first", index=False)
        pd.DataFrame({"b": [3, 4, 5]}).to_excel(writer, sheet_name="second", index=False)
    return buf.getvalue()


def test_excel_sheets_are_listed_and_selectable():
    raw = _two_sheet_xlsx()
    assert list_sources(raw, "x.xlsx") == ["first", "second"]
    assert read_file_to_df(raw, "x.xlsx", source="second").shape == (3, 1)
    assert read_file_to_df(raw, "x.xlsx").shape == (2, 1)


def test_sqlite_tables_are_listed_and_selectable(tmp_path):
    path = tmp_path / "t.db"
    conn = sqlite3.connect(path)
    pd.DataFrame({"a": [1]}).to_sql("one", conn, index=False)
    pd.DataFrame({"b": [1, 2]}).to_sql("two", conn, index=False)
    conn.close()
    raw = path.read_bytes()
    assert sorted(list_sources(raw, "t.db")) == ["one", "two"]
    assert read_file_to_df(raw, "t.db", source="two").shape == (2, 1)
    with pytest.raises(ValueError, match="not found"):
        read_file_to_df(raw, "t.db", source="missing; DROP TABLE one")


def test_single_table_formats_have_no_sources():
    assert list_sources(b"a,b\n1,2\n", "x.csv") == []
