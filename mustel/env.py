# mustel/env.py
"""
mustel env — Python environment detection.

Returns structured JSON (not emoji output).
Used by `mustel env` CLI command and the MCP server's env() tool.
"""

from __future__ import annotations

import sys
import platform
import subprocess
from typing import Dict, Any


def _run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=10)
    except Exception:
        return None


def _get_venv_status() -> Dict[str, Any]:
    """Detect virtual environment status."""
    in_venv = sys.prefix != sys.base_prefix
    return {
        "active": in_venv,
        "path": sys.prefix if in_venv else None,
        "base_python": sys.base_prefix,
    }


def _get_pip_info() -> Dict[str, Any]:
    """Get pip version and location."""
    out = _run_cmd([sys.executable, "-m", "pip", "--version"])
    if out:
        parts = out.strip().split()
        return {
            "version": parts[1] if len(parts) > 1 else "unknown",
            "available": True,
        }
    return {"version": None, "available": False}


def get_env_snapshot() -> Dict[str, Any]:
    """
    Return a complete snapshot of the current Python environment.

    This is what `mustel env` returns and the MCP env() tool exposes.
    """
    venv = _get_venv_status()
    pip = _get_pip_info()

    return {
        "python_version": sys.version.split()[0],
        "python_path": sys.executable,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
        "venv": venv,
        "pip": pip,
    }
