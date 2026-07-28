"""
Regression test for a real bug: setting OBJC_DISABLE_INITIALIZE_FORK_SAFETY
from inside an already-running process is too late on macOS, the runtime
already read it at process start. RQ's per-job worker subprocess crashed
with an Objective-C fork-safety error until this was fixed to re-exec the
process with the variable set from birth. This test mocks os.execve so it
never actually replaces the test process.
"""

import os
from unittest.mock import patch

from core.fork_safety import ensure_fork_safety_env


def test_no_reexec_when_already_set():
    with patch.dict(os.environ, {"OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES"}):
        with patch("os.execve") as mock_execve:
            result = ensure_fork_safety_env()
        mock_execve.assert_not_called()
        assert result is False


def test_reexec_triggered_when_missing():
    env_copy = os.environ.copy()
    env_copy.pop("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", None)
    with patch.dict(os.environ, env_copy, clear=True):
        with patch("os.execve") as mock_execve:
            ensure_fork_safety_env()
            mock_execve.assert_called_once()
            args, kwargs = mock_execve.call_args
            passed_env = args[2]
            assert passed_env.get("OBJC_DISABLE_INITIALIZE_FORK_SAFETY") == "YES"