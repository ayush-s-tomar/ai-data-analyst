import sys
import types

from file_readers import MAX_PDF_PAGES, read_file_to_df


class _Page:
    def extract_tables(self):
        return []

    def extract_text(self):
        return "a line of text"


class _Pdf:
    pages = [_Page() for _ in range(100)]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_only_the_first_pages_of_a_pdf_are_read(monkeypatch):
    fake = types.ModuleType("pdfplumber")
    fake.open = lambda _stream: _Pdf()
    monkeypatch.setitem(sys.modules, "pdfplumber", fake)
    df = read_file_to_df(b"%PDF-fake", "doc.pdf")
    assert len(df) == MAX_PDF_PAGES
