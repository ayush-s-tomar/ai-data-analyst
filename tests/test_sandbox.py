import pandas as pd
import pytest

from sandbox import CodeRejected, run_user_code, validate_code


@pytest.fixture
def df():
    return pd.DataFrame({"region": ["N", "S", "N", "S"], "revenue": [10, 20, 30, 40]})


# ---- static validation ----
@pytest.mark.parametrize("code", [
    "import os",
    "import subprocess",
    "from os import path",
    "open('secret.txt').read()",
    "__import__('os').system('echo hi')",
    "eval('1+1')",
    "exec('x=1')",
    "pd.read_csv('/etc/passwd')",
    "df.to_csv('out.csv')",
    "plt.savefig('x.png')",
    "x = df.__class__",
    "x = ().__class__.__bases__",
    "'{0.__init__}'.format(df)",
    "getattr(df, 'shape')",
    "pd.io.common.get_handle('x', 'r')",
    "matplotlib.os.system('echo hi')",
    "class A: pass",
    "from pandas import *",
    "import numpy as np\nnp.load('x.npy')",
    "import seaborn as sns\nsns.load_dataset('tips')",
])
def test_dangerous_code_is_rejected(code):
    with pytest.raises(CodeRejected):
        validate_code(code)


@pytest.mark.parametrize("code", [
    "import pandas as pd\nprint(df.groupby('region')['revenue'].sum())",
    "import matplotlib.pyplot as plt\nplt.bar(df['region'], df['revenue'])\nplt.title('t')",
    "import numpy as np\nprint(np.mean(df['revenue']))",
    "from collections import Counter\nprint(Counter(df['region']))",
    "print('{:.2f}'.format(3.14159))",
    "print(f'total={df.revenue.sum()}')",
])
def test_normal_analysis_code_is_accepted(code):
    validate_code(code)


def test_empty_and_too_long_code_rejected():
    with pytest.raises(CodeRejected):
        validate_code("   ")
    with pytest.raises(CodeRejected):
        validate_code("x = 1\n" * 10_000)


# ---- real execution in the isolated subprocess ----
def test_runs_grouped_sum(df):
    out = run_user_code("print(df.groupby('region')['revenue'].sum().to_dict())", df)
    assert out["error"] is None
    assert "{'N': 40, 'S': 60}" in out["output"]


def test_returns_chart_png(df):
    code = "plt.bar(df['region'], df['revenue'])\nplt.title('Revenue')"
    out = run_user_code(code, df)
    assert out["error"] is None
    assert len(out["charts"]) == 1
    assert out["charts"][0][:8] == b"\x89PNG\r\n\x1a\n"


def test_original_dataframe_is_not_modified(df):
    run_user_code("df['revenue'] = 0", df)
    assert df["revenue"].tolist() == [10, 20, 30, 40]


def test_runtime_error_is_reported_not_raised(df):
    out = run_user_code("print(df['missing_column'])", df)
    assert out["error"] and "KeyError" in out["error"]


def test_rejected_code_never_runs(df):
    out = run_user_code("import os\nprint(os.getcwd())", df)
    assert out["error"] and "safety check" in out["error"]
    assert out["output"] == ""


def test_infinite_loop_is_stopped(df):
    out = run_user_code("while True:\n    pass", df, timeout=3)
    assert out["error"] and "stopped" in out["error"]


def test_api_key_is_not_inherited_by_worker(df, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_super_secret_value")
    out = run_user_code("print('ok')", df)
    assert out["error"] is None
    assert "gsk_super_secret_value" not in (out["output"] or "")