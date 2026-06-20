# mustel/runner.py
"""
mustel runner — the main orchestrator.

Coordinates all engines in parallel, handles file caching,
performs adaptive mode selection (Dev vs Audit), and invokes JS/TS/Notebook linters.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from mustel.schema import MustelReport
from mustel.normalizer import normalize, _count_python_files
from mustel.engines import ruff_engine, bandit_engine, pipaudit_engine, oxlint_engine
from mustel.patterns import loader as pattern_loader
from mustel.cache import MustelCache


def _detect_audit_mode() -> bool:
    """
    Detect if Mustel is running in a git hook (pre-commit) or a CI/CD environment.
    If so, we run in Audit Mode (enabling security/CVE audits).
    """
    return (
        os.environ.get("GIT_DIR") is not None or
        os.environ.get("GIT_INDEX_FILE") is not None or
        os.environ.get("CI") is not None or
        os.environ.get("GITHUB_ACTIONS") is not None or
        os.environ.get("PRE_COMMIT") is not None
    )


def _find_all_files(path: str) -> tuple[List[str], List[str], int]:
    """
    Recursively find all Python, Notebook, and JS/TS files in a directory.
    Returns: (python_files, js_files, total_python_count)
    """
    py_files = []
    js_files = []
    py_count = 0

    if os.path.isfile(path):
        if path.endswith(".py") or path.endswith(".ipynb"):
            return [path], [], 1
        elif path.endswith((".js", ".jsx", ".ts", ".tsx")):
            return [], [path], 0
        return [], [], 0

    for root, dirs, files in os.walk(path):
        # Skip standard non-project directories
        dirs[:] = [
            d for d in dirs
            if d not in {".venv", "venv", "env", ".env", "__pycache__",
                          ".git", ".tox", "node_modules", "dist", "build"}
        ]
        for fname in files:
            full_path = os.path.join(root, fname)
            if fname.endswith(".py") or fname.endswith(".ipynb"):
                py_files.append(full_path)
                py_count += 1
            elif fname.endswith((".js", ".jsx", ".ts", ".tsx")):
                js_files.append(full_path)

    return py_files, js_files, py_count


def run_review(
    path: Optional[str] = None,
    single_file: Optional[str] = None,
    skip_packages: bool = False,
    audit: Optional[bool] = None,
) -> MustelReport:
    """
    Run a mustel review. Detects files, checks caching, runs active engines in parallel,
    and returns a normalized schema report.
    """
    # Resolve project root and scan path
    if single_file:
        scan_path = os.path.abspath(single_file)
        project_root = os.path.dirname(scan_path)
    elif path:
        scan_path = os.path.abspath(path)
        project_root = scan_path
    else:
        scan_path = os.getcwd()
        project_root = scan_path

    scanned_at = datetime.now(timezone.utc).isoformat()
    start_time = time.monotonic()

    # Determine mode: default to Dev unless explicitly requested or hook/CI detected
    audit_mode = audit if audit is not None else _detect_audit_mode()

    # Initialize cache
    cache = MustelCache(project_root)

    # Find files to scan
    py_files, js_files, files_scanned = _find_all_files(scan_path)

    # Caching check
    python_to_scan = []
    js_to_scan = []
    cached_findings: List[Dict[str, Any]] = []

    for f in py_files:
        cached = cache.get_cached_findings(f)
        if cached is not None:
            cached_findings.extend(cached)
        else:
            python_to_scan.append(f)

    for f in js_files:
        cached = cache.get_cached_findings(f)
        if cached is not None:
            cached_findings.extend(cached)
        else:
            js_to_scan.append(f)

    # Executing active engines in parallel on changed files
    ruff_results = []
    bandit_results = []
    pattern_results = []
    pipaudit_results = []
    oxlint_results = []

    # Run scanners if there are changed files
    if python_to_scan or js_to_scan or (audit_mode and not skip_packages):
        with ThreadPoolExecutor() as executor:
            futures = {}

            if python_to_scan:
                futures["ruff"] = executor.submit(ruff_engine.run, python_to_scan, project_root)
                futures["patterns"] = executor.submit(pattern_loader.run, python_to_scan, project_root)
                if audit_mode:
                    futures["bandit"] = executor.submit(bandit_engine.run, python_to_scan, project_root)

            if js_to_scan:
                futures["oxlint"] = executor.submit(oxlint_engine.run, js_to_scan, project_root, audit_mode)

            if audit_mode and not skip_packages:
                futures["pipaudit"] = executor.submit(pipaudit_engine.run)

            # Gather results from threads
            if "ruff" in futures:
                try:
                    ruff_results = futures["ruff"].result() or []
                except Exception:
                    pass
            if "patterns" in futures:
                try:
                    pattern_results = futures["patterns"].result() or []
                except Exception:
                    pass
            if "bandit" in futures:
                try:
                    bandit_results = futures["bandit"].result() or []
                except Exception:
                    pass
            if "oxlint" in futures:
                try:
                    oxlint_results = futures["oxlint"].result() or []
                except Exception:
                    pass
            if "pipaudit" in futures:
                try:
                    pipaudit_results = futures["pipaudit"].result() or []
                except Exception:
                    pass

        # Update cache for the scanned files
        # Group new findings by relative file path to cache them correctly
        new_findings_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for f in python_to_scan + js_to_scan:
            try:
                rel_p = os.path.relpath(f, project_root)
            except ValueError:
                rel_p = f
            new_findings_by_file[rel_p] = []

        all_new_code_findings = ruff_results + bandit_results + pattern_results + oxlint_results
        for finding in all_new_code_findings:
            f_path = finding.get("file", "")
            if f_path in new_findings_by_file:
                new_findings_by_file[f_path].append(finding)

        # Write updates to cache object
        for rel_p, findings in new_findings_by_file.items():
            abs_p = os.path.abspath(os.path.join(project_root, rel_p))
            cache.update_cached_findings(abs_p, findings)

        cache.save()

    # Combine cached findings with newly detected ones
    combined_code_findings = cached_findings + ruff_results + bandit_results + pattern_results + oxlint_results

    # Split findings back into the original lists expected by normalizer
    final_ruff = []
    final_bandit = []
    final_patterns = []

    for issue in combined_code_findings:
        engine = issue.get("engine", "")
        if engine == "ruff" or engine == "oxlint":
            final_ruff.append(issue)
        elif engine == "bandit":
            final_bandit.append(issue)
        elif engine == "mustel-patterns":
            final_patterns.append(issue)

    scan_duration_ms = int((time.monotonic() - start_time) * 1000)

    # Normalize results and return schema-compliant report
    return normalize(
        ruff_results=final_ruff,
        bandit_results=final_bandit,
        pattern_results=final_patterns,
        pipaudit_results=pipaudit_results,
        project_root=project_root,
        scan_duration_ms=scan_duration_ms,
        files_scanned=files_scanned,
        scanned_at=scanned_at,
    )
