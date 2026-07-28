import os
import sys


def ensure_fork_safety_env():
    """
    macOS crashes RQ's per-job forked worker processes with an Objective-C
    fork-safety error unless this env var is set before the process image
    starts. Setting it from inside an already-running process is too late,
    the runtime already read it at startup. The only reliable fix is
    re-executing the current process with the variable set from birth.
    Returns False if already set (safe to continue). Never returns True
    in practice, since execve replaces the process entirely.
    """
    if os.environ.get("OBJC_DISABLE_INITIALIZE_FORK_SAFETY") == "YES":
        return False
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    os.execve(sys.executable, [sys.executable] + sys.argv, os.environ)
    return True