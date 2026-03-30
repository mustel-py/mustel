# mustel/runner.py
"""
mustel runner — the main orchestrator.

Coordinates all engines, collects results, passes to normalizer.
This is what `mustel review` calls under the hood.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

from mustel.schema import MustelReport
from mustel.normalizer import normalize, _count_python_files
from mustel.engines import ruff_engine, bandit_engine, pipaudit_engine
from mustel.patterns import loader as pattern_loader


def run_review(
    path: Optional[str] = None,
    single_file: Optional[str] = None,
    skip_packages: bool = False,
) -> MustelReport:
    """
    Run a full mustel review on a directory or file.

    Args:
        path:          Directory to scan (defaults to current working directory).
        single_file:   If set, only scan this one file (used by --file flag).
        skip_packages: If True, skip pip-audit (faster, no network).

    Returns:
        MustelReport conforming to schema v1.
    """
    # Resolve the path
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

    # Count files before scanning (for the report)
    files_scanned = _count_python_files(scan_path)

    # Run all engines
    ruff_results = []
    bandit_results = []
    pattern_results = []
    pipaudit_results = []

    try:
        ruff_results = ruff_engine.run(scan_path, project_root=project_root)
    except Exception:
        pass

    try:
        bandit_results = bandit_engine.run(scan_path, project_root=project_root)
    except Exception:
        pass

    try:
        pattern_results = pattern_loader.run(scan_path, project_root=project_root)
    except Exception:
        pass

    if not skip_packages:
        try:
            pipaudit_results = pipaudit_engine.run()
        except Exception:
            pass

    # Calculate duration
    scan_duration_ms = int((time.monotonic() - start_time) * 1000)

    # Normalize and return
    return normalize(
        ruff_results=ruff_results,
        bandit_results=bandit_results,
        pattern_results=pattern_results,
        pipaudit_results=pipaudit_results,
        project_root=project_root,
        scan_duration_ms=scan_duration_ms,
        files_scanned=files_scanned,
        scanned_at=scanned_at,
    )
