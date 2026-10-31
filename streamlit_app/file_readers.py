"""File parsing helpers for AI Data Analyst (no Streamlit imports, so they are unit-testable)."""
from __future__ import annotations

import io
import json
import os
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

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


_READERS = {
    ".csv": lambda c, e: pd.read_csv(io.BytesIO(c)),
    ".tsv": lambda c, e: pd.read_csv(io.BytesIO(c), sep="\t"),
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


def read_file_to_df(contents: bytes, filename: str) -> pd.DataFrame:
    """Parse an uploaded file into a DataFrame. Raises ValueError for unsupported/empty files."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext or 'unknown'}")
    if not contents:
        raise ValueError("The file is empty")
    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise ValueError(f"The file is larger than {MAX_FILE_MB} MB")

    df = _READERS[ext](contents, ext)

    if df.empty:
        raise ValueError("No rows were found in the file")
    return ensure_unique_columns(df)


def df_to_string(df: pd.DataFrame, max_rows: int = 50, max_stat_columns: int = 40) -> str:
    """Compact text description of a DataFrame to give the model context."""
    info = [
        f"Shape: {df.shape[0]} rows x {df.shape[1]} columns",
        f"\nColumns: {list(df.columns)}",
        f"\nDtypes:\n{df.dtypes.to_string()}",
        f"\nFirst {min(max_rows, len(df))} rows:\n{df.head(max_rows).to_string()}",
        f"\nBasic Statistics:\n{df.iloc[:, :max_stat_columns].describe(include='all').to_string()}",
    ]
    null_counts = df.isnull().sum()
    if null_counts.any():
        info.append(f"\nNull counts:\n{null_counts[null_counts > 0].to_string()}")
    return "\n".join(info)