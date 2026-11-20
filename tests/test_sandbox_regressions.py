import pandas as pd
import pytest

from sandbox import CodeRejected, run_user_code, validate_code


@pytest.mark.parametrize("code", [
    "import socket", "import pickle", "import ctypes", "import importlib", "import builtins",
    "import os.path", "import sys", "from pathlib import Path", "from os.path import join",
    "exit()", "quit()", "input()", "breakpoint()", "help()", "vars(df)", "globals()", "locals()",
    "setattr(df, 'a', 1)", "delattr(df, 'a')", "memoryview(b'')", "compile('1', 'x', 'eval')",
    "df.to_pickle('x')", "df.to_sql('t', None)", "df.eval('a')",
    "pd.read_json('x')", "import numpy as np\nnp.fromfile('x')", "import numpy as np\nnp.savetxt('x', [1])",
    "import matplotlib.pyplot as plt\nplt.savefig('x')",
    "df.__dict__", "().__class__.__mro__", "x = lambda: 0\ny = x.__globals__",
    "async def f():\n    pass", "x = 'a__b'", "__import__('os')",
])
def test_known_escape_routes_stay_blocked(code):
    with pytest.raises(CodeRejected):
        validate_code(code)


@pytest.mark.parametrize("code", [
    "import seaborn as sns\nsns.barplot(data=df, x='region', y='revenue')",
    "print(df.groupby('region').agg({'revenue': 'sum'}).reset_index())",
    "print(df.sort_values('revenue', ascending=False).head(3))",
    "print(df['region'].str.upper().value_counts())",
    "print(pd.to_datetime(df['d']).dt.month.value_counts())",
    "import math\nprint(math.sqrt(4))",
    "import statistics\nprint(statistics.mean([1, 2]))",
    "from datetime import datetime\nprint(datetime(2024, 1, 1))",
    "print(f'{df.shape[0]:,} rows')",
    "print(df.describe().T)",
    "print(df.iloc[0])",
])
def test_ordinary_analysis_code_is_not_over_blocked(code):
    validate_code(code)


def test_output_is_capped():
    out = run_user_code("print('x' * 100000)", pd.DataFrame({"a": [1]}))
    assert out["error"] is None and len(out["output"]) <= 20_000


def test_chart_count_is_capped():
    code = "for i in range(10):\n    plt.figure()\n    plt.plot([1, 2])"
    out = run_user_code(code, pd.DataFrame({"a": [1]}))
    assert out["error"] is None and len(out["charts"]) == 6
