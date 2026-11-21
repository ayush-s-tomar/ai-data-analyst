from limits import MAX_QUESTION_CHARS, clean_question


def test_whitespace_is_collapsed():
    assert clean_question("  total \n\n revenue\t by   region ") == "total revenue by region"


def test_length_is_capped():
    assert len(clean_question("x" * 5000)) == MAX_QUESTION_CHARS


def test_empty_values_become_empty_string():
    assert clean_question(None) == "" and clean_question("   ") == ""
