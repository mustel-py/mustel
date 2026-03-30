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


def _is_ruff_available() -> bool:
    """Check if ruff is installed and callable."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _ensure_ruff() -> bool:
    """Install ruff if not present. Returns True if available after check."""
    if _is_ruff_available():
        return True
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "ruff>=0.4.0", "-q"],
            capture_output=True, timeout=60
        )
        return _is_ruff_available()
    except Exception:
        return False


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


def run(path: str, project_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run ruff on a path (file or directory) and return normalized mustel issues.

    Args:
        path: File or directory to scan.
        project_root: Root directory for making paths relative (defaults to path
                      if it's a dir, else dirname of path).

    Returns:
        List of normalized issue dicts (no IDs yet — assigned by normalizer).
        Returns empty list if ruff is unavailable or finds no issues.
    """
    if project_root is None:
        project_root = path if os.path.isdir(path) else os.path.dirname(path)

    if not _ensure_ruff():
        return []

    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check",
                path,
                "--output-format=json",
                "--exit-zero",                  # don't fail on findings
                "--select", "E,F,B,S,ANN,ASYNC,W",
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
