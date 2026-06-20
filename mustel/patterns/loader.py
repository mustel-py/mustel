# mustel/patterns/loader.py
"""
Pattern loader — reads YAML pattern files and matches them against Python source.

Supports three detection types:
  1. keyword  — simple substring match on each line
  2. pattern  — regex match on each line
  3. function_call_missing_arg — detects function calls missing a required argument
                                  (uses regex heuristics, not full AST)

YAML pattern file format:
  module: <module_name>
  version_min: "3.0"    (optional)
  patterns:
    - id: "unique-pattern-id"
      severity: "high" | "medium" | "warning" | "low"
      category: "security" | "bug" | "style"
      cwe: "CWE-89"     (optional)
      detect:
        type: "keyword" | "pattern" | "function_call_missing_arg"
        match: "<string>"                    (for keyword/pattern)
        function: "<func.name>"              (for function_call_missing_arg)
        functions: [...]                     (list variant)
        missing_arg: "<arg_name>"            (for function_call_missing_arg)
      message: "Human-readable explanation."
      docs: "https://..."                    (optional)
"""

from __future__ import annotations

import os
import re
import glob
from typing import List, Dict, Any, Optional

import yaml


# ─────────────────────────────────────────────
#  YAML loading
# ─────────────────────────────────────────────

_PATTERNS_DIR = os.path.dirname(__file__)


def _load_all_pattern_files() -> List[Dict[str, Any]]:
    """Load all YAML pattern files from the patterns directory."""
    yaml_files = glob.glob(os.path.join(_PATTERNS_DIR, "*.yaml"))
    all_patterns = []
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and isinstance(data, dict) and "patterns" in data:
                module_name = data.get("module", os.path.basename(yaml_file).replace(".yaml", ""))
                for pattern in data["patterns"]:
                    pattern["_module"] = module_name
                    all_patterns.append(pattern)
        except Exception:
            continue
    return all_patterns


# ─────────────────────────────────────────────
#  Detection engines
# ─────────────────────────────────────────────

def _detect_keyword(source_lines: List[str], match_str: str) -> List[int]:
    """Return 1-indexed line numbers where match_str is found (case-sensitive)."""
    return [
        i + 1
        for i, line in enumerate(source_lines)
        if match_str in line
    ]


def _detect_pattern(source_lines: List[str], pattern_str: str) -> List[int]:
    """Return 1-indexed line numbers matching a regex pattern."""
    try:
        compiled = re.compile(pattern_str)
    except re.error:
        return []
    return [
        i + 1
        for i, line in enumerate(source_lines)
        if compiled.search(line)
    ]


def _detect_function_call_missing_arg(
    source_lines: List[str],
    functions: List[str],
    missing_arg: str,
) -> List[int]:
    """
    Detect function calls that are missing a specific keyword argument.

    Heuristic: find lines containing <function_name>( that do NOT
    contain the missing_arg keyword anywhere in the call block.

    This is a multi-line heuristic: we look at the call line and
    up to 5 following lines to handle multi-line calls.
    """
    hits = []
    source = "\n".join(source_lines)

    for func in functions:
        # Escape dots for regex (e.g. "requests.get" -> "requests\.get")
        escaped = re.escape(func)
        # Find all call sites
        for i, line in enumerate(source_lines):
            if re.search(rf"\b{escaped}\s*\(", line):
                # Gather the call context (current + next 5 lines)
                context_end = min(i + 6, len(source_lines))
                context = " ".join(source_lines[i:context_end])
                # Check if the missing arg is present in the call context
                if missing_arg not in context:
                    hits.append(i + 1)  # 1-indexed

    return hits


# ─────────────────────────────────────────────
#  Import detection (which modules a file uses)
# ─────────────────────────────────────────────

def _get_imported_modules(source_lines: List[str]) -> set:
    """
    Extract top-level module names imported in a Python file.

    Covers:
      import requests
      import requests.adapters
      from requests import ...
      from requests.auth import ...
    """
    modules = set()
    import_re = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*)")
    for line in source_lines:
        match = import_re.match(line)
        if match:
            full_module = match.group(1)
            # Take just the top-level name (e.g. "requests" from "requests.adapters")
            modules.add(full_module.split(".")[0])
    return modules


# ─────────────────────────────────────────────
#  Main scan function
# ─────────────────────────────────────────────

def _load_ipynb_source(file_path: str) -> List[str]:
    """Extract raw source lines from code cells of a Jupyter Notebook (.ipynb)."""
    import json
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        lines = []
        for cell in data.get("cells", []):
            if cell.get("cell_type") == "code":
                cell_source = cell.get("source", [])
                if isinstance(cell_source, list):
                    for line in cell_source:
                        lines.append(line.rstrip("\n"))
                elif isinstance(cell_source, str):
                    lines.extend(cell_source.splitlines())
        return lines
    except Exception:
        return []


def _scan_file(
    file_path: str,
    patterns: List[Dict[str, Any]],
    project_root: str,
) -> List[Dict[str, Any]]:
    """
    Scan one Python file or Jupyter Notebook against all loaded patterns.
    """
    if file_path.endswith(".ipynb"):
        source_lines = _load_ipynb_source(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source_lines = f.read().splitlines()
        except Exception:
            return []

    imported_modules = _get_imported_modules(source_lines)

    try:
        rel_file = os.path.relpath(file_path, project_root)
    except ValueError:
        rel_file = file_path

    issues = []

    for pattern in patterns:
        module = pattern.get("_module", "")

        # Skip if this file doesn't import the relevant module
        # Exception: patterns with module="*" match all files
        if module != "*" and module not in imported_modules:
            continue

        detect = pattern.get("detect", {})
        detect_type = detect.get("type", "keyword")
        pat_id = pattern.get("id", "unknown")
        severity = pattern.get("severity", "warning")
        category = pattern.get("category", "bug")
        cwe = pattern.get("cwe", "")
        message = pattern.get("message", "")

        hit_lines: List[int] = []

        if detect_type == "keyword":
            match_str = detect.get("match", "")
            if match_str:
                hit_lines = _detect_keyword(source_lines, match_str)

        elif detect_type in ("pattern", "regex"):
            match_str = detect.get("match", "")
            if match_str:
                hit_lines = _detect_pattern(source_lines, match_str)

        elif detect_type == "function_call_missing_arg":
            # Accept either "function" (str) or "functions" (list)
            functions = detect.get("functions") or []
            single = detect.get("function")
            if single:
                functions = [single]
            missing_arg = detect.get("missing_arg", "")
            if functions and missing_arg:
                hit_lines = _detect_function_call_missing_arg(
                    source_lines, functions, missing_arg
                )

        for line_no in hit_lines:
            issues.append({
                "file": rel_file,
                "line": line_no,
                "col": 1,
                "severity": severity,
                "category": category,
                "rule": pat_id,
                "message": message,
                "engine": "mustel-patterns",
                "module_context": module,
                "cwe": cwe,
                "fix_available": False,
            })

    return issues


def run(path: str | List[str], project_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run all loaded patterns against a file, directory, or list of files.

    Args:
        path: File, directory, or list of files to scan.
        project_root: Root for relative paths.

    Returns:
        List of normalized issue dicts.
    """
    if not path:
        return []

    if project_root is None:
        first_path = path[0] if isinstance(path, list) else path
        project_root = first_path if os.path.isdir(first_path) else os.path.dirname(first_path)

    patterns = _load_all_pattern_files()
    if not patterns:
        return []

    py_files: List[str] = []

    if isinstance(path, list):
        for p in path:
            if p.endswith(".py") or p.endswith(".ipynb"):
                py_files.append(p)
    else:
        if os.path.isfile(path):
            if path.endswith(".py") or path.endswith(".ipynb"):
                py_files = [path]
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                # Skip common non-project directories
                dirs[:] = [
                    d for d in dirs
                    if d not in {".venv", "venv", "env", ".env", "__pycache__",
                                  ".git", ".tox", "node_modules", "dist", "build"}
                ]
                for fname in files:
                    if fname.endswith(".py") or fname.endswith(".ipynb"):
                        py_files.append(os.path.join(root, fname))

    issues = []
    for py_file in py_files:
        issues.extend(_scan_file(py_file, patterns, project_root))

    return issues
