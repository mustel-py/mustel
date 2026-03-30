# mustel/env.py
"""
mustel env — Python environment detection.

Returns structured JSON (not emoji output).
Used by `mustel env` CLI command and the MCP server's env() tool.
"""

from __future__ import annotations

import sys
import os
import platform
import subprocess
import json
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


def _get_installed_packages() -> Dict[str, str]:
    """Get dict of {package: version} for the current environment."""
    out = _run_cmd([sys.executable, "-m", "pip", "list", "--format=json"])
    if not out:
        return {}
    try:
        data = json.loads(out)
        return {pkg["name"].lower(): pkg["version"] for pkg in data}
    except Exception:
        return {}


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


def check_package(package_name: str) -> Dict[str, Any]:
    """
    Check if a package is available.

    Returns:
        {
            "available": bool,
            "version": str | null,
            "importable": bool,
        }
    """
    import importlib.util

    packages = _get_installed_packages()
    name_lower = package_name.lower()

    in_pip = name_lower in packages
    version = packages.get(name_lower)

    importable = importlib.util.find_spec(package_name) is not None

    return {
        "package": package_name,
        "available": in_pip or importable,
        "version": version,
        "importable": importable,
    }


def install_package(package_name: str) -> Dict[str, Any]:
    """
    Install a package using the current Python's pip.

    Returns:
        {
            "success": bool,
            "message": str,
            "package": str,
        }
    """
    # Check if already installed
    check = check_package(package_name)
    if check["available"]:
        return {
            "success": True,
            "message": f"{package_name} is already installed (version {check['version']})",
            "package": package_name,
            "already_installed": True,
        }

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Successfully installed {package_name}",
                "package": package_name,
                "already_installed": False,
            }
        else:
            return {
                "success": False,
                "message": result.stderr or "Installation failed",
                "package": package_name,
                "already_installed": False,
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "package": package_name,
            "already_installed": False,
        }


def create_venv(path: str = ".venv") -> Dict[str, Any]:
    """
    Create a virtual environment.

    Returns:
        {
            "success": bool,
            "path": str,
            "message": str,
        }
    """
    abs_path = os.path.abspath(path)

    if os.path.exists(abs_path):
        return {
            "success": False,
            "path": abs_path,
            "message": f"Directory already exists at {abs_path}",
        }

    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", abs_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return {
                "success": True,
                "path": abs_path,
                "message": f"Virtual environment created at {abs_path}",
            }
        else:
            return {
                "success": False,
                "path": abs_path,
                "message": result.stderr or "Failed to create venv",
            }
    except Exception as e:
        return {
            "success": False,
            "path": abs_path,
            "message": str(e),
        }


def get_venv_status(directory: str = ".") -> Dict[str, Any]:
    """
    Get the venv status for a project directory.

    Returns:
        {
            "exists": bool,
            "active": bool,
            "name": str | null,
            "path": str | null,
        }
    """
    cwd = os.path.abspath(directory)
    venv_names = [".venv", "venv", "env", ".env"]

    for name in venv_names:
        venv_path = os.path.join(cwd, name)
        cfg_file = os.path.join(venv_path, "pyvenv.cfg")
        if os.path.exists(cfg_file):
            active_prefix = os.path.normcase(os.path.realpath(sys.prefix))
            venv_real = os.path.normcase(os.path.realpath(venv_path))
            return {
                "exists": True,
                "active": active_prefix == venv_real,
                "name": name,
                "path": venv_path,
            }

    return {
        "exists": False,
        "active": sys.prefix != sys.base_prefix,
        "name": None,
        "path": None,
    }
