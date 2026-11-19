from file_readers import read_file_to_df


def test_cp1252_csv_is_decoded():
    raw = "name,city\nJosé,Zürich\n".encode("cp1252")
    df = read_file_to_df(raw, "a.csv")
    assert df.shape == (1, 2) and df.iloc[0, 0] == "José"


def test_utf8_bom_csv():
    raw = b"\xef\xbb\xbfa,b\n1,2\n"
    assert list(read_file_to_df(raw, "a.csv").columns) == ["a", "b"]


def test_semicolon_and_pipe_delimiters_are_sniffed():
    assert read_file_to_df(b"a;b\n1;2\n3;4\n", "a.csv").shape == (2, 2)
    assert read_file_to_df(b"a|b\n1|2\n3|4\n", "a.csv").shape == (2, 2)
