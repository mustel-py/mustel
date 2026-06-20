# mustel/engines/ruff_engine.py
"""
ruff engine — bug and style detection.

Runs: ruff check <path> --output-format=json --exit-zero
Parses ruff's JSON, normalizes to mustel schema dicts.

Rules enabled:
  E   — pycodestyle errors
  F   — pyflakes (undefined names, unused imports, etc.)
  B   — bugbear (common bugs and anti-patterns)
  S   — bandit-mirrored security rules
  ANN — type annotation issues (warnings only)
  ASYNC — async/await misuse
"""

from __future__ import annotations

import subprocess
import sys
import json
import os
from typing import List, Dict, Any, Optional


# ─────────────────────────────────────────────
#  ruff severity mapping
#  ruff doesn't expose severity per-issue, so we infer from rule prefix.
# ─────────────────────────────────────────────

_RULE_TO_SEVERITY: Dict[str, str] = {
    "E": "error",       # pycodestyle errors
    "F": "error",       # pyflakes
    "B": "error",       # bugbear
    "S": "high",        # security (bandit-mirror)
    "ANN": "warning",   # type annotations
    "ASYNC": "error",   # async misuse
    "W": "warning",     # pycodestyle warnings
    "C": "warning",     # complexity
    "N": "warning",     # naming
    "I": "warning",     # isort
    "UP": "warning",    # pyupgrade
    "RUF": "warning",   # ruff-specific
}

_RULE_TO_CATEGORY: Dict[str, str] = {
    "E": "bug",
    "F": "bug",
    "B": "bug",
    "S": "security",
    "ANN": "style",
    "ASYNC": "bug",
    "W": "style",
    "C": "style",
    "N": "style",
    "I": "style",
    "UP": "style",
    "RUF": "bug",
}


def _infer_severity(rule_code: str) -> str:
    prefix = _get_prefix(rule_code)
    return _RULE_TO_SEVERITY.get(prefix, "warning")


def _infer_category(rule_code: str) -> str:
    prefix = _get_prefix(rule_code)
    return _RULE_TO_CATEGORY.get(prefix, "style")


def _get_prefix(rule_code: str) -> str:
    """Extract the letter prefix from a rule code like 'E501' → 'E'."""
    for i, ch in enumerate(rule_code):
        if ch.isdigit():
            return rule_code[:i]
    return rule_code


_RUFF_CMD: Optional[List[str]] = None


def _get_ruff_cmd() -> Optional[List[str]]:
    """Get the command to execute Ruff (binary on PATH preferred, fallback to module)."""
    global _RUFF_CMD
    if _RUFF_CMD is not None:
        return _RUFF_CMD

    # Check PATH first (binary is much faster than sys.executable startup)
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            _RUFF_CMD = ["ruff"]
            return _RUFF_CMD
    except Exception:
        pass

    # Check python module fallback
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            _RUFF_CMD = [sys.executable, "-m", "ruff"]
            return _RUFF_CMD
    except Exception:
        pass

    return None


def _normalize_issue(raw: Dict[str, Any], project_root: str) -> Optional[Dict[str, Any]]:
    """
    Normalize one ruff issue dict to the mustel schema format.

    ruff JSON shape:
    {
        "code": "F821",
        "filename": "/abs/path/to/file.py",
        "location": {"row": 10, "column": 4},
        "end_location": {"row": 10, "column": 10},
        "message": "Undefined name `foo`",
        "fix": null | {"message": "...", "edits": [...]},
        "url": "https://..."
    }
    """
    try:
        rule_code = raw.get("code") or "UNKNOWN"
        abs_file = raw.get("filename", "")
        # Make path relative to project root for cleaner output
        try:
            rel_file = os.path.relpath(abs_file, project_root)
        except ValueError:
            rel_file = abs_file

        location = raw.get("location", {})
        line = location.get("row", 1)
        col = location.get("column", 1)

        message = raw.get("message", "")
        fix = raw.get("fix")
        fix_available = fix is not None

        return {
            "file": rel_file,
            "line": line,
            "col": col,
            "severity": _infer_severity(rule_code),
            "category": _infer_category(rule_code),
            "rule": rule_code,
            "message": message,
            "engine": "ruff",
            "module_context": "",
            "cwe": "",
            "fix_available": fix_available,
        }
    except Exception:
        return None


def run(path: str | List[str], project_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run ruff on a path (file, directory, or list of files) and return normalized issues.
    """
    if not path:
        return []

    if project_root is None:
        first_path = path[0] if isinstance(path, list) else path
        project_root = first_path if os.path.isdir(first_path) else os.path.dirname(first_path)

    cmd = _get_ruff_cmd()
    if not cmd:
        return []

    paths_to_check = path if isinstance(path, list) else [path]

    try:
        result = subprocess.run(
            cmd + [
                "check",
            ] + paths_to_check + [
                "--output-format=json",
                "--exit-zero",                  # don't fail on findings
                "--select", "E,F,B,S,ANN,ASYNC,W,PD,NPY",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if not result.stdout.strip():
            return []

        raw_issues = json.loads(result.stdout)
        issues = []
        for raw in raw_issues:
            normalized = _normalize_issue(raw, project_root)
            if normalized:
                issues.append(normalized)

        return issues

    except json.JSONDecodeError:
        return []
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []
