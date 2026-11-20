import pandas as pd

from cache import AnswerCache, df_fingerprint, make_key


def test_same_data_and_question_share_a_key_regardless_of_spacing_and_case():
    df = pd.DataFrame({"a": [1, 2]})
    assert make_key(df, "Total  A?") == make_key(df.copy(), "total a?")


def test_changed_data_or_hidden_columns_change_the_key():
    df = pd.DataFrame({"a": [1, 2]})
    assert make_key(df, "q") != make_key(pd.DataFrame({"a": [1, 3]}), "q")
    assert make_key(df, "q") != make_key(df, "q", hidden=["a"])


def test_unhashable_cells_do_not_crash():
    assert df_fingerprint(pd.DataFrame({"x": [[1], [2]]}))


def test_cache_evicts_oldest_and_returns_none_on_miss():
    cache = AnswerCache(max_items=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert cache.get("b") is None and cache.get("a") == 1 and cache.get("c") == 3
