# mustel/normalizer.py
"""
mustel normalizer — merges all engine outputs into one schema-compliant JSON report.

Takes raw output from:
  - ruff_engine.run()         → list of issue dicts
  - bandit_engine.run()       → list of issue dicts
  - pipaudit_engine.run()     → list of vulnerability dicts
  - patterns/loader.run()     → list of issue dicts

Does:
  1. Deduplication — same file + same line from multiple engines → keep one
  2. Categorization — routes to errors[], security[], warnings[]
  3. ID assignment — E001, E002... S001, S002... W001... P001...
  4. agent_prompt generation — plain English summary for AI agents
  5. Summary calculation — totals, clean flag, highest severity

Returns: complete MustelReport object
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

import mustel
from mustel.schema import (
    MustelIssue,
    PackageVulnerability,
    MustelResults,
    MustelSummary,
    MustelReport,
    SEVERITY_RANK,
    highest_severity,
)


# ─────────────────────────────────────────────
#  Deduplication
# ─────────────────────────────────────────────

def _make_dedup_key(issue: Dict[str, Any]) -> Tuple[str, int]:
    """
    Create a deduplication key for an issue.

    Two issues with the same file + line are considered duplicates.
    The one with higher severity (or 'bandit' origin) wins.
    """
    return (issue.get("file", ""), issue.get("line", 0))


def _deduplicate(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate issues (same file + line from multiple engines).

    Priority: bandit > mustel-patterns > ruff (for same-line dupes)
    """
    _ENGINE_PRIORITY = {"bandit": 0, "mustel-patterns": 1, "ruff": 2}

    seen: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for issue in issues:
        key = _make_dedup_key(issue)
        if key not in seen:
            seen[key] = issue
        else:
            # Keep the one from higher-priority engine
            existing_priority = _ENGINE_PRIORITY.get(seen[key].get("engine", ""), 99)
            new_priority = _ENGINE_PRIORITY.get(issue.get("engine", ""), 99)
            if new_priority < existing_priority:
                seen[key] = issue

    return list(seen.values())


# ─────────────────────────────────────────────
#  Categorization
# ─────────────────────────────────────────────

def _categorize_issue(issue: Dict[str, Any]) -> str:
    """Return 'error', 'security', or 'warning' bucket for an issue."""
    severity = issue.get("severity", "warning")
    category = issue.get("category", "style")

    if category == "security" or severity in ("high", "critical"):
        return "security"
    if severity == "error" or category == "bug":
        return "error"
    return "warning"


# ─────────────────────────────────────────────
#  ID assignment
# ─────────────────────────────────────────────

def _assign_ids(
    errors: List[Dict[str, Any]],
    security: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
    packages: List[Dict[str, Any]],
) -> Tuple[List[MustelIssue], List[MustelIssue], List[MustelIssue], List[PackageVulnerability]]:
    """Assign sequential IDs to each bucket and convert dicts to dataclasses."""

    def _to_issue(d: Dict[str, Any], prefix: str, n: int) -> MustelIssue:
        return MustelIssue(
            id=f"{prefix}{n:03d}",
            file=d.get("file", ""),
            line=d.get("line", 1),
            col=d.get("col", 1),
            severity=d.get("severity", "warning"),
            category=d.get("category", "bug"),
            rule=d.get("rule", ""),
            message=d.get("message", ""),
            engine=d.get("engine", ""),
            module_context=d.get("module_context", ""),
            cwe=d.get("cwe", ""),
            fix_available=d.get("fix_available", False),
        )

    def _to_vuln(d: Dict[str, Any], n: int) -> PackageVulnerability:
        return PackageVulnerability(
            id=f"P{n:03d}",
            package=d.get("package", ""),
            installed_version=d.get("installed_version", ""),
            severity=d.get("severity", "medium"),
            category="vulnerability",
            cve=d.get("cve", ""),
            fixed_version=d.get("fixed_version", ""),
            message=d.get("message", ""),
            engine="pip-audit",
        )

    error_issues = [_to_issue(d, "E", i + 1) for i, d in enumerate(errors)]
    security_issues = [_to_issue(d, "S", i + 1) for i, d in enumerate(security)]
    warning_issues = [_to_issue(d, "W", i + 1) for i, d in enumerate(warnings)]
    pkg_vulns = [_to_vuln(d, i + 1) for i, d in enumerate(packages)]

    return error_issues, security_issues, warning_issues, pkg_vulns


# ─────────────────────────────────────────────
#  agent_prompt generation
# ─────────────────────────────────────────────

def _generate_agent_prompt(
    errors: List[MustelIssue],
    security: List[MustelIssue],
    warnings: List[MustelIssue],
    packages: List[PackageVulnerability],
) -> str:
    """
    Generate the ultra-compressed plain English agent_prompt string.
    Target length: < 200 characters.
    """
    total = len(errors) + len(security) + len(warnings) + len(packages)

    if total == 0:
        return "mustel found 0 issues. Project clean."

    groups = []
    
    high_sec = [s.id for s in security if s.severity in ("high", "critical")]
    if high_sec: groups.append(f"HighSec:{','.join(high_sec)}")
        
    pkg_id = [p.id for p in packages]
    if pkg_id: groups.append(f"PkgVuln:{','.join(pkg_id)}")
    
    errs = [e.id for e in errors]
    if errs: groups.append(f"Errs:{','.join(errs)}")
        
    med_sec = [s.id for s in security if s.severity not in ("high", "critical")]
    if med_sec: groups.append(f"MedSec:{','.join(med_sec)}")
        
    warns = [w.id for w in warnings]
    if warns: groups.append(f"Warns:{','.join(warns)}")

    return f"mustel found {total} issues: {' | '.join(groups)}. Use IDs to lookup details in JSON."


# ─────────────────────────────────────────────
#  File counting
# ─────────────────────────────────────────────

def _count_python_files(path: str) -> int:
    """Count Python files in a path."""
    if os.path.isfile(path):
        return 1 if path.endswith(".py") else 0
    count = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [
            d for d in dirs
            if d not in {".venv", "venv", "env", ".env", "__pycache__",
                          ".git", ".tox", "node_modules", "dist", "build"}
        ]
        count += sum(1 for f in files if f.endswith(".py"))
    return count


# ─────────────────────────────────────────────
#  Main normalize function
# ─────────────────────────────────────────────

def normalize(
    ruff_results: List[Dict[str, Any]],
    bandit_results: List[Dict[str, Any]],
    pattern_results: List[Dict[str, Any]],
    pipaudit_results: List[Dict[str, Any]],
    project_root: str,
    scan_duration_ms: int,
    files_scanned: int,
    scanned_at: str,
) -> MustelReport:
    """
    Merge all engine results into a single MustelReport.

    Args:
        ruff_results:     Output from ruff_engine.run()
        bandit_results:   Output from bandit_engine.run()
        pattern_results:  Output from patterns/loader.run()
        pipaudit_results: Output from pipaudit_engine.run()
        project_root:     Absolute path that was scanned
        scan_duration_ms: How long the scan took
        files_scanned:    Number of Python files scanned
        scanned_at:       ISO 8601 timestamp of scan

    Returns:
        MustelReport conforming to schema v1
    """
    # Combine all code-level issues
    all_code_issues = ruff_results + bandit_results + pattern_results

    # Deduplicate
    deduped = _deduplicate(all_code_issues)

    # Categorize into buckets
    error_dicts = []
    security_dicts = []
    warning_dicts = []

    for issue in deduped:
        bucket = _categorize_issue(issue)
        if bucket == "error":
            error_dicts.append(issue)
        elif bucket == "security":
            security_dicts.append(issue)
        else:
            warning_dicts.append(issue)

    # Sort each bucket by file then line
    def _sort_key(d: Dict[str, Any]):
        return (d.get("file", ""), d.get("line", 0))

    error_dicts.sort(key=_sort_key)
    security_dicts.sort(key=_sort_key)
    warning_dicts.sort(key=_sort_key)

    # Assign IDs and convert to dataclasses
    errors, security, warnings, packages = _assign_ids(
        error_dicts, security_dicts, warning_dicts, pipaudit_results
    )

    # Calculate summary
    all_severities = (
        [e.severity for e in errors]
        + [s.severity for s in security]
        + [w.severity for w in warnings]
        + [p.severity for p in packages]
    )
    highest = highest_severity(all_severities)
    total = len(errors) + len(security) + len(warnings) + len(packages)

    summary = MustelSummary(
        total_errors=len(errors),
        total_security=len(security),
        total_warnings=len(warnings),
        total_package_vulnerabilities=len(packages),
        clean=(total == 0),
        highest_severity=highest,
    )

    # Generate agent prompt
    agent_prompt = _generate_agent_prompt(errors, security, warnings, packages)

    # Build report
    return MustelReport(
        mustel_version=mustel.__version__,
        schema_version=mustel.__schema_version__,
        scanned_at=scanned_at,
        project_root=project_root,
        files_scanned=files_scanned,
        scan_duration_ms=scan_duration_ms,
        results=MustelResults(
            errors=errors,
            security=security,
            warnings=warnings,
            packages=packages,
        ),
        summary=summary,
        agent_prompt=agent_prompt,
    )
