"""Restricted execution of AI-generated analysis code.

This is defence in depth, not a perfect sandbox:

1. Static validation (AST): only allow-listed imports, no dunder/private
   attribute access, no file/system/network helpers, no dangerous builtins.
2. Restricted builtins and a guarded ``__import__`` while the code runs.
3. The code runs in a separate Python process with a scrubbed environment
   (API keys are not inherited), a wall-clock timeout, and CPU/file-size
   limits on POSIX systems.

Use ``run_user_code(code, df)`` from the app. The same file doubles as the
worker entry point: ``python -I sandbox.py --worker``.
"""
from __future__ import annotations

import ast
import base64
import builtins
import contextlib
import io
import json
import os
import pickle
import subprocess
import sys
import tempfile
import traceback

MAX_CODE_CHARS = 20_000
MAX_OUTPUT_CHARS = 20_000
MAX_CHARTS = 6
DEFAULT_TIMEOUT_SECONDS = 25
RESULT_MARKER = "@@SANDBOX_RESULT@@"

ALLOWED_IMPORTS = {
    "pandas", "numpy", "matplotlib", "seaborn",
    "math", "statistics", "datetime", "collections", "itertools",
    "functools", "re", "string", "decimal", "fractions", "calendar",
    "textwrap", "warnings",
}

BLOCKED_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "getattr", "setattr",
    "delattr", "globals", "locals", "vars", "input", "breakpoint", "exit",
    "quit", "help", "memoryview", "os", "sys", "subprocess", "builtins",
    "importlib", "shutil", "socket", "pickle", "ctypes", "pathlib",
}

# Attribute names that reach the file system, network, process or interpreter.
BLOCKED_ATTRS = {
    "os", "sys", "subprocess", "builtins", "importlib", "shutil", "socket",
    "pickle", "ctypes", "pathlib", "io", "system", "popen", "environ",
    "getenv", "spawn", "fork", "exec", "eval", "compile", "open",
    "get_handle", "urlopen", "urlretrieve", "request", "urllib",
    "load", "loads", "load_dataset", "loadtxt", "genfromtxt", "fromfile",
    "fromregex", "tofile", "memmap", "save", "savez", "savez_compressed",
    "savetxt", "savefig", "imsave", "imread", "to_csv", "to_excel",
    "to_pickle", "to_parquet", "to_feather", "to_hdf", "to_sql",
    "to_clipboard", "to_stata", "to_orc",
}

SAFE_BUILTIN_NAMES = [
    "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter",
    "float", "format", "frozenset", "int", "isinstance", "len", "list",
    "map", "max", "min", "next", "iter", "pow", "print", "range", "repr",
    "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple",
    "zip", "chr", "ord", "bin", "hex", "oct", "callable", "hash",
    "Exception", "ValueError", "KeyError", "TypeError", "IndexError",
    "ZeroDivisionError", "ArithmeticError", "AttributeError",
    "StopIteration", "RuntimeError", "NotImplementedError",
    "True", "False", "None",
]


class CodeRejected(Exception):
    """Raised when generated code fails the safety validation."""


def _top_level(module: str) -> str:
    return module.split(".")[0]


def validate_code(code: str) -> ast.AST:
    """Parse and validate code; return the AST or raise CodeRejected."""
    if not isinstance(code, str) or not code.strip():
        raise CodeRejected("no code to run")
    if len(code) > MAX_CODE_CHARS:
        raise CodeRejected("code is too long")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise CodeRejected(f"syntax error: {exc.msg} (line {exc.lineno})") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _top_level(alias.name) not in ALLOWED_IMPORTS:
                    raise CodeRejected(f"import of '{alias.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if node.level or not node.module or _top_level(node.module) not in ALLOWED_IMPORTS:
                raise CodeRejected(f"import from '{node.module}' is not allowed")
            if any(alias.name == "*" for alias in node.names):
                raise CodeRejected("wildcard imports are not allowed")
        elif isinstance(node, ast.Name):
            if node.id in BLOCKED_NAMES or node.id.startswith("__"):
                raise CodeRejected(f"use of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise CodeRejected(f"access to private attribute '{node.attr}' is not allowed")
            if node.attr in BLOCKED_ATTRS or node.attr.startswith("read_"):
                raise CodeRejected(f"use of '.{node.attr}' is not allowed")
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str) and "__" in node.value:
                raise CodeRejected("strings containing '__' are not allowed")
        elif isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Await)):
            raise CodeRejected("class definitions and async code are not allowed")
    return tree


def _safe_builtins() -> dict:
    safe = {name: getattr(builtins, name) for name in SAFE_BUILTIN_NAMES if hasattr(builtins, name)}

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
        if level != 0 or _top_level(name) not in ALLOWED_IMPORTS:
            raise ImportError(f"import of '{name}' is not allowed")
        return builtins.__import__(name, globals, locals, fromlist, level)

    safe["__import__"] = guarded_import
    return safe


def _execute(code: str, df) -> dict:
    """Run validated code in the current process (called inside the worker)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    result = {"output": "", "charts": [], "error": None}
    try:
        tree = validate_code(code)
        plt.close("all")
        namespace = {
            "__builtins__": _safe_builtins(),
            "__name__": "analysis",
            "df": df.copy(),
            "pd": pd, "np": np, "plt": plt, "sns": sns,
        }
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile(tree, "<analysis>", "exec"), namespace)  # noqa: S102
        result["output"] = buffer.getvalue()[:MAX_OUTPUT_CHARS]
        for number in plt.get_fignums()[:MAX_CHARTS]:
            figure = plt.figure(number)
            png = io.BytesIO()
            figure.savefig(png, format="png", dpi=100, bbox_inches="tight",
                           facecolor="white", edgecolor="none")
            result["charts"].append(base64.b64encode(png.getvalue()).decode("ascii"))
        plt.close("all")
    except CodeRejected as exc:
        result["error"] = f"Code rejected by safety check: {exc}"
    except BaseException as exc:  # noqa: BLE001 - report any failure to the caller
        tb = traceback.format_exc(limit=3)
        result["error"] = f"{type(exc).__name__}: {exc}\n{tb}"[:2000]
    return result


def _limit_resources(timeout: int) -> None:
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (timeout + 2, timeout + 4))
        resource.setrlimit(resource.RLIMIT_FSIZE, (20_000_000, 20_000_000))
    except Exception:  # noqa: BLE001 - not available on Windows
        pass


def _worker_main() -> None:
    payload = pickle.loads(sys.stdin.buffer.read())  # produced by our own parent process
    _limit_resources(int(payload.get("timeout", DEFAULT_TIMEOUT_SECONDS)))
    keep = {"PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "MPLBACKEND", "MPLCONFIGDIR", "PYTHONIOENCODING"}
    for key in list(os.environ):
        if key not in keep:
            del os.environ[key]
    result = _execute(payload["code"], payload["df"])
    sys.__stdout__.write(RESULT_MARKER + json.dumps(result) + "\n")
    sys.__stdout__.flush()


def _clean_env(workdir: str) -> dict:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": workdir,
        "HOME": workdir,
        "TEMP": workdir,
        "TMP": workdir,
        "PYTHONIOENCODING": "utf-8",
    }
    if os.environ.get("SYSTEMROOT"):
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


def run_user_code(code: str, df, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Validate and run generated code in an isolated subprocess.

    Returns {"output": str, "charts": [png bytes], "error": str | None}.
    """
    try:
        validate_code(code)
    except CodeRejected as exc:
        return {"output": "", "charts": [], "error": f"Code rejected by safety check: {exc}"}

    payload = pickle.dumps({"code": code, "df": df, "timeout": timeout}, protocol=4)
    with tempfile.TemporaryDirectory(prefix="ada_sandbox_") as workdir:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", os.path.abspath(__file__), "--worker"],
                input=payload, capture_output=True, timeout=timeout,
                env=_clean_env(workdir), cwd=workdir, check=False,
            )
        except subprocess.TimeoutExpired:
            return {"output": "", "charts": [],
                    "error": f"The analysis took longer than {timeout} seconds and was stopped."}

    text = proc.stdout.decode("utf-8", errors="replace")
    for line in reversed(text.splitlines()):
        if line.startswith(RESULT_MARKER):
            data = json.loads(line[len(RESULT_MARKER):])
            data["charts"] = [base64.b64decode(item) for item in data.get("charts", [])]
            return data
    detail = proc.stderr.decode("utf-8", errors="replace").strip()[-500:]
    return {"output": "", "charts": [],
            "error": "The analysis process ended without a result." + (f" Details: {detail}" if detail else "")}


if __name__ == "__main__":
    if "--worker" in sys.argv:
        _worker_main()
