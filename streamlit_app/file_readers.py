"""File parsing helpers for AI Data Analyst (no Streamlit imports, so they are unit-testable)."""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sqlite3
import tempfile
import defusedxml.ElementTree as ET

import pandas as pd

MAX_FILE_MB = 25

# Pickle files are deliberately NOT supported: unpickling untrusted data can execute arbitrary code.
SUPPORTED_EXTENSIONS = [
    ".csv", ".xlsx", ".xls", ".tsv", ".json", ".parquet", ".xml",
    ".db", ".sqlite", ".sqlite3", ".pdf", ".ods", ".feather",
]


def ensure_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip column names, replace blanks and make duplicates unique (a, a_2, a_3)."""
    seen: dict[str, int] = {}
    names = []
    for position, raw in enumerate(df.columns, start=1):
        name = str(raw).strip() if raw is not None else ""
        if not name or name.lower() == "none" or name.lower() == "nan":
            name = f"column_{position}"
        count = seen.get(name, 0) + 1
        seen[name] = count
        names.append(name if count == 1 else f"{name}_{count}")
    df = df.copy()
    df.columns = names
    return df


def _read_json(contents: bytes) -> pd.DataFrame:
    try:
        return pd.read_json(io.BytesIO(contents))
    except Exception:  # noqa: BLE001 - fall back to manual parsing
        data = json.loads(contents)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            if any(isinstance(v, list) for v in data.values()):
                return pd.DataFrame(data)
            return pd.DataFrame([data])
        raise ValueError("Cannot convert this JSON structure to a table")


def _read_xml(contents: bytes) -> pd.DataFrame:
    try:
        return pd.read_xml(io.BytesIO(contents))
    except Exception:  # noqa: BLE001 - fall back to manual parsing
        root = ET.fromstring(contents)
        records = [{sub.tag: sub.text for sub in child} for child in root]
        if not records:
            records = [{child.tag: child.text for child in root}]
        return pd.DataFrame(records)


def _read_sqlite(contents: bytes, ext: str) -> pd.DataFrame:
    tmp_path = None
    conn = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        conn = sqlite3.connect(tmp_path)
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        if tables.empty:
            raise ValueError("No tables found in the SQLite database")
        table_name = tables["name"].iloc[0].replace("]", "]]")
        return pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
    finally:
        if conn is not None:
            conn.close()
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _read_pdf(contents: bytes) -> pd.DataFrame:
    try:
        import pdfplumber
    except ImportError as exc:
        raise ValueError("PDF support requires pdfplumber. Add it to requirements.txt") from exc

    rows: list = []
    lines: list[str] = []
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if table:
                    rows.extend(table)
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    if len(rows) > 1:
        header, body = rows[0], rows[1:]
        width = len(header)
        body = [r[:width] + [None] * (width - len(r)) for r in body]
        return pd.DataFrame(body, columns=header)
    return pd.DataFrame({"text": [line for line in lines if line.strip()]})


def _decode_text(contents: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    return contents.decode("latin-1")


def _read_csv(contents: bytes, sep=None) -> pd.DataFrame:
    """Decode with fallbacks (utf-8, cp1252, latin-1) and sniff the delimiter when not given."""
    text = _decode_text(contents)
    if sep is None:
        try:
            sep = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|").delimiter
        except csv.Error:
            sep = ","
    return pd.read_csv(io.StringIO(text), sep=sep)


_READERS = {
    ".csv": lambda c, e: _read_csv(c),
    ".tsv": lambda c, e: _read_csv(c, "\t"),
    ".xlsx": lambda c, e: pd.read_excel(io.BytesIO(c)),
    ".xls": lambda c, e: pd.read_excel(io.BytesIO(c)),
    ".ods": lambda c, e: pd.read_excel(io.BytesIO(c), engine="odf"),
    ".json": lambda c, e: _read_json(c),
    ".parquet": lambda c, e: pd.read_parquet(io.BytesIO(c)),
    ".feather": lambda c, e: pd.read_feather(io.BytesIO(c)),
    ".xml": lambda c, e: _read_xml(c),
    ".db": lambda c, e: _read_sqlite(c, e),
    ".sqlite": lambda c, e: _read_sqlite(c, e),
    ".sqlite3": lambda c, e: _read_sqlite(c, e),
    ".pdf": lambda c, e: _read_pdf(c),
}


def _sqlite_read(contents: bytes, ext: str, table=None):
    """Return (table names, DataFrame of `table` or None)."""
    tmp_path = None
    conn = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        conn = sqlite3.connect(tmp_path)
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        frame = None
        if table is not None:
            if table not in names:
                raise ValueError(f"Table not found: {table}")
            frame = pd.read_sql("SELECT * FROM [" + table.replace("]", "]]") + "]", conn)
        return names, frame
    finally:
        if conn is not None:
            conn.close()
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def list_sources(contents: bytes, filename: str) -> list:
    """Sheet names (Excel/ODS) or table names (SQLite). Empty list for single-table formats."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".xlsx", ".xls", ".ods"):
        engine = "odf" if ext == ".ods" else None
        return list(pd.ExcelFile(io.BytesIO(contents), engine=engine).sheet_names)
    if ext in (".db", ".sqlite", ".sqlite3"):
        return _sqlite_read(contents, ext)[0]
    return []


def read_file_to_df(contents: bytes, filename: str, source=None) -> pd.DataFrame:
    """Parse an uploaded file into a DataFrame. Raises ValueError for unsupported/empty files."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext or 'unknown'}")
    if not contents:
        raise ValueError("The file is empty")
    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise ValueError(f"The file is larger than {MAX_FILE_MB} MB")

    if source is not None and ext in (".xlsx", ".xls", ".ods"):
        df = pd.read_excel(io.BytesIO(contents), sheet_name=source, engine="odf" if ext == ".ods" else None)
    elif source is not None and ext in (".db", ".sqlite", ".sqlite3"):
        df = _sqlite_read(contents, ext, source)[1]
    else:
        df = _READERS[ext](contents, ext)

    if df.empty:
        raise ValueError("No rows were found in the file")
    return ensure_unique_columns(df)


def data_quality(df: pd.DataFrame) -> dict:
    """Cheap health check shown to the user before the first question."""
    nulls = df.isnull().sum()
    try:
        duplicates = int(df.duplicated().sum())
    except TypeError:  # unhashable cells such as lists from JSON
        duplicates = 0
    text_numbers = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            values = series.dropna()
            if len(values) and pd.to_numeric(values, errors="coerce").notna().mean() > 0.9:
                text_numbers.append(str(column))
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "duplicate_rows": duplicates,
        "missing_cells": int(nulls.sum()),
        "columns_with_missing": {str(k): int(v) for k, v in nulls[nulls > 0].items()},
        "numbers_stored_as_text": text_numbers,
    }


def _shorten(frame: pd.DataFrame, max_cols: int = 40, max_chars: int = 60) -> pd.DataFrame:
    """Cap columns and truncate long text cells so the model prompt stays small."""
    view = frame.iloc[:, :max_cols].copy()
    for column in view.columns:
        series = view[column]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            view[column] = series.map(lambda v: v[:max_chars] + "..." if isinstance(v, str) and len(v) > max_chars else v)
    return view


SENSITIVE_TOKENS = {"email", "phone", "mobile", "aadhaar", "aadhar", "ssn", "password", "passport", "pan", "address", "dob", "iban"}


def sensitive_columns(df: pd.DataFrame) -> list:
    """Columns whose name contains a sensitive word (matched on whole words, so 'company' is safe)."""
    found = []
    for column in df.columns:
        words = set(re.split(r"[^a-z0-9]+", str(column).lower()))
        if words & SENSITIVE_TOKENS:
            found.append(column)
    return found


def _mask(df: pd.DataFrame, hidden) -> pd.DataFrame:
    if not hidden:
        return df
    view = df.copy()
    for column in hidden:
        if column in view.columns:
            view[column] = "<hidden>"
    return view


def clean_numeric_text(df: pd.DataFrame, columns) -> pd.DataFrame:
    """Turn text such as '1,200' or '$300' into numbers. Cells that still fail become missing."""
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            continue
        cleaned = result[column].map(lambda v: re.sub(r"[,\s$%\u20b9\u20ac\u00a3]", "", v) if isinstance(v, str) else v)
        result[column] = pd.to_numeric(cleaned, errors="coerce")
    return result


def df_to_string(df: pd.DataFrame, max_rows: int = 50, max_stat_columns: int = 40, hidden=()) -> str:
    """Compact text description of a DataFrame to give the model context."""
    shown = _mask(df, hidden)
    info = [
        f"Shape: {df.shape[0]} rows x {df.shape[1]} columns",
        f"\nColumns: {list(df.columns)}",
        f"\nDtypes:\n{df.dtypes.to_string()}",
        f"\nFirst {min(max_rows, len(df))} rows:\n{_shorten(shown.head(max_rows)).to_string()}",
        f"\nBasic Statistics:\n{_shorten(shown.iloc[:, :max_stat_columns].describe(include='all')).to_string()}",
    ]
    null_counts = df.isnull().sum()
    if null_counts.any():
        info.append(f"\nNull counts:\n{null_counts[null_counts > 0].to_string()}")
    return "\n".join(info)
