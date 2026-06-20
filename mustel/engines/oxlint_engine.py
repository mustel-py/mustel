# mustel/engines/oxlint_engine.py
"""
oxlint engine — sub-millisecond JS/TS linter execution using oxlint.
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
from typing import List, Dict, Any, Optional

_OXLINT_CMD: Optional[List[str]] = None


def _get_oxlint_cmd(audit_mode: bool = False) -> Optional[List[str]]:
    global _OXLINT_CMD
    if _OXLINT_CMD is not None:
        return _OXLINT_CMD

    # Check local node_modules first
    local_bin = os.path.abspath(os.path.join("node_modules", ".bin", "oxlint"))
    if os.path.exists(local_bin):
        _OXLINT_CMD = [local_bin]
        return _OXLINT_CMD

    # Check Windows cmd fallback
    local_bin_win = local_bin + ".cmd"
    if os.path.exists(local_bin_win):
        _OXLINT_CMD = [local_bin_win]
        return _OXLINT_CMD

    # Check PATH
    if shutil.which("oxlint"):
        _OXLINT_CMD = ["oxlint"]
        return _OXLINT_CMD

    # Audit mode allows npx fallback (might check network)
    if audit_mode and shutil.which("npx"):
        # npx on Windows needs shell or .cmd suffix
        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
        if shutil.which(npx_cmd):
            _OXLINT_CMD = [npx_cmd, "-y", "oxlint"]
            return _OXLINT_CMD

    return None


def run(files: List[str], project_root: str, audit_mode: bool = False) -> List[Dict[str, Any]]:
    """Run oxlint on a list of JS/TS files and return normalized issues."""
    if not files:
        return []

    cmd = _get_oxlint_cmd(audit_mode)
    if not cmd:
        return []

    try:
        # Run oxlint with json output formatting
        result = subprocess.run(
            cmd + ["-f", "json"] + files,
            capture_output=True,
            text=True,
            shell=(sys.platform == "win32"),  # Needed for cmd/batch scripts on Windows
            timeout=30,
        )

        output = result.stdout.strip()
        if not output:
            return []

        data = json.loads(output)
        issues = []

        for raw in data:
            filename = raw.get("filename", "")
            try:
                rel_file = os.path.relpath(filename, project_root)
            except ValueError:
                rel_file = filename

            severity = "error" if raw.get("severity") == "error" else "warning"
            category = "bug" if severity == "error" else "style"

            issues.append({
                "file": rel_file,
                "line": raw.get("start", {}).get("line", 1),
                "col": raw.get("start", {}).get("column", 1),
                "severity": severity,
                "category": category,
                "rule": raw.get("ruleName", "oxlint-rule"),
                "message": raw.get("message", ""),
                "engine": "oxlint",
                "module_context": "",
                "cwe": "",
                "fix_available": False,
            })

        return issues

    except Exception:
        return []
