import os
import shutil

import pandas as pd
import pytest

from sandbox import _worker_command, docker_command, run_user_code


def test_docker_command_is_locked_down():
    cmd = docker_command("img")
    joined = " ".join(cmd)
    assert "--network none" in joined and "--read-only" in joined and "--cap-drop ALL" in joined
    assert "img" in cmd and cmd[-3:] == ["-I", "/app/sandbox.py", "--worker"]


def test_default_mode_is_subprocess_without_secrets(monkeypatch):
    monkeypatch.delenv("SANDBOX_MODE", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret")
    command, env = _worker_command("/tmp/x")
    assert command[0] != "docker" and "GROQ_API_KEY" not in env


def test_docker_mode_is_selected_by_env(monkeypatch):
    monkeypatch.setenv("SANDBOX_MODE", "docker")
    assert _worker_command("/tmp/x")[0][0] == "docker"


@pytest.mark.skipif(not (shutil.which("docker") and os.environ.get("ADA_TEST_DOCKER")),
                    reason="set ADA_TEST_DOCKER=1 and build the ai-data-analyst image to run this")
def test_worker_runs_inside_container(monkeypatch):
    monkeypatch.setenv("SANDBOX_MODE", "docker")
    out = run_user_code("print(df['a'].sum())", pd.DataFrame({"a": [1, 2]}), timeout=60)
    assert out["error"] is None and "3" in out["output"]
