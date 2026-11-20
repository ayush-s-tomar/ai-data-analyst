import io
import zipfile

import pandas as pd
import pytest

from file_readers import _check_zip_safe, read_file_to_df


def _zip_of_zeros(size=200_000):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("big.xml", b"0" * size)
    return buf.getvalue()


def test_high_compression_ratio_is_refused():
    with pytest.raises(ValueError, match="compression"):
        _check_zip_safe(_zip_of_zeros())


def test_unpacked_size_limit_is_enforced():
    with pytest.raises(ValueError, match="too much data"):
        _check_zip_safe(_zip_of_zeros(), max_uncompressed=1000)


def test_normal_excel_file_still_loads():
    buf = io.BytesIO()
    pd.DataFrame({"a": [1, 2, 3]}).to_excel(buf, index=False)
    assert read_file_to_df(buf.getvalue(), "ok.xlsx").shape == (3, 1)


def test_non_zip_bytes_are_ignored_by_the_guard():
    _check_zip_safe(b"plain text, not a zip")
