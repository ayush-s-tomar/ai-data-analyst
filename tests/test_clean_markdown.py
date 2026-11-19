from analyst import clean_markdown


def test_clean_markdown_removes_br_tags():
    table = "| Region | Detail |\n|---|---|\n| North | sales=120 <br>- South: 60 |"
    cleaned = clean_markdown(table)
    assert "<br" not in cleaned
    assert "sales=120; - South: 60" in cleaned
    assert clean_markdown("Line one<br>Line two").splitlines() == ["Line one", "Line two"]
