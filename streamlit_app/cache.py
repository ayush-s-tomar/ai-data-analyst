"""In-session cache for first-turn answers, keyed by data, question and hidden columns."""
import hashlib
from collections import OrderedDict

import pandas as pd


def df_fingerprint(df: pd.DataFrame) -> str:
    h = hashlib.sha256()
    h.update("|".join(map(str, df.columns)).encode("utf-8"))
    try:
        h.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    except TypeError:  # unhashable cells such as lists
        h.update(df.astype(str).to_csv().encode("utf-8"))
    return h.hexdigest()


def make_key(df: pd.DataFrame, question: str, hidden=()) -> tuple:
    return (df_fingerprint(df), " ".join(str(question).split()).lower(), tuple(sorted(map(str, hidden))))


class AnswerCache:
    def __init__(self, max_items: int = 30):
        self.max_items = max_items
        self._items = OrderedDict()

    def get(self, key):
        if key in self._items:
            self._items.move_to_end(key)
            return self._items[key]
        return None

    def put(self, key, value) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self.max_items:
            self._items.popitem(last=False)
