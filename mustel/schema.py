# mustel/schema.py
"""
mustel Schema v1 — The locked JSON output contract.

This schema is the single source of truth for all mustel output.
Every engine, the normalizer, the CLI, and the MCP server all
produce and consume this exact structure.

NEVER change this schema without bumping schema_version.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional

import mustel  # for __version__


# ─────────────────────────────────────────────
#  Issue Types
# ─────────────────────────────────────────────

@dataclass
class MustelIssue:
    """
    A single code-level issue found by any engine or pattern.

    Covers: bugs (ruff), security findings (bandit / mustel-patterns).
    """
    id: str                        # e.g. "E001", "S003", "W002"
    file: str                      # relative path to file
    line: int                      # 1-indexed line number
    col: int                       # 1-indexed column number
    severity: str                  # "error" | "warning" | "high" | "medium" | "low"
    category: str                  # "bug" | "security" | "style" | "vulnerability"
    rule: str                      # engine rule name e.g. "undefined-variable"
    message: str                   # human-readable explanation
    engine: str                    # "ruff" | "bandit" | "mustel-patterns"
    module_context: str = ""       # which Python module triggered this, e.g. "sqlite3"
    cwe: str = ""                  # CWE ID if applicable, e.g. "CWE-89"
    fix_available: bool = False    # whether ruff can auto-fix this


@dataclass
class PackageVulnerability:
    """
    A CVE-level vulnerability found in an installed package by pip-audit.
    """
    id: str                        # e.g. "P001"
    package: str                   # package name
    installed_version: str         # currently installed version
    severity: str                  # "critical" | "high" | "medium" | "low"
    category: str = "vulnerability"
    cve: str = ""                  # CVE ID, e.g. "CVE-2023-32681"
    fixed_version: str = ""        # version that fixes it (if known)
    message: str = ""              # human-readable explanation
    engine: str = "pip-audit"


@dataclass
class MustelSummary:
    """
    Aggregate counts for one mustel scan.
    """
    total_errors: int = 0
    total_security: int = 0
    total_warnings: int = 0
    total_package_vulnerabilities: int = 0
    clean: bool = True
    highest_severity: str = "none"  # "none" | "low" | "medium" | "high" | "critical" | "error"


@dataclass
class MustelResults:
    """
    The categorized results bucket inside a MustelReport.
    """
    errors: List[MustelIssue] = field(default_factory=list)
    security: List[MustelIssue] = field(default_factory=list)
    warnings: List[MustelIssue] = field(default_factory=list)
    packages: List[PackageVulnerability] = field(default_factory=list)


@dataclass
class MustelReport:
    """
    The complete mustel scan report — schema v1.

    This is the top-level object returned by mustel.review()
    and output by `mustel review` on the CLI.
    """
    mustel_version: str
    schema_version: int
    scanned_at: str               # ISO 8601 UTC
    project_root: str             # absolute path that was scanned
    files_scanned: int
    scan_duration_ms: int
    results: MustelResults
    summary: MustelSummary
    agent_prompt: str             # pre-written plain English for the AI agent

    def to_dict(self) -> dict:
        """Convert to a plain dict, ready for json.dumps()."""
        d = asdict(self)
        return d

    def to_compact_dict(self) -> dict:
        """Return a token-optimized representation of the report."""
        def _compact_issue(issue):
            return {
                "id": issue.id,
                "file": issue.file,
                "line": issue.line,
                "msg": issue.message,
            }
        def _compact_vuln(vuln):
            return {
                "id": vuln.id,
                "pkg": vuln.package,
                "ver": vuln.installed_version,
                "msg": vuln.message,
            }
        
        return {
            "summary": {
                "errs": self.summary.total_errors,
                "sec": self.summary.total_security,
                "warns": self.summary.total_warnings,
                "vulns": self.summary.total_package_vulnerabilities,
            },
            "errors": [_compact_issue(i) for i in self.results.errors],
            "security": [_compact_issue(i) for i in self.results.security],
            "warnings": [_compact_issue(i) for i in self.results.warnings],
            "packages": [_compact_vuln(p) for p in self.results.packages],
            "prompt": self.agent_prompt
        }

    def to_json(self, indent: int = 2, compact: bool = False) -> str:
        """Serialize to JSON string."""
        data = self.to_compact_dict() if compact else self.to_dict()
        return json.dumps(data, indent=indent)

    @property
    def is_clean(self) -> bool:
        return self.summary.clean


# ─────────────────────────────────────────────
#  Severity Helpers
# ─────────────────────────────────────────────

# Severity rank — higher number = more severe
SEVERITY_RANK = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "warning": 2,
    "high": 3,
    "error": 3,
    "critical": 4,
}


def highest_severity(severities: List[str]) -> str:
    """Return the most severe severity string from a list."""
    if not severities:
        return "none"
    return max(severities, key=lambda s: SEVERITY_RANK.get(s, 0))


# ─────────────────────────────────────────────
#  Report Builder
# ─────────────────────────────────────────────

def build_empty_report(project_root: str) -> MustelReport:
    """Build a clean, zero-issue report (used as baseline before engines run)."""
    return MustelReport(
        mustel_version=mustel.__version__,
        schema_version=mustel.__schema_version__,
        scanned_at=datetime.now(timezone.utc).isoformat(),
        project_root=project_root,
        files_scanned=0,
        scan_duration_ms=0,
        results=MustelResults(),
        summary=MustelSummary(clean=True, highest_severity="none"),
        agent_prompt="mustel found no issues. The project looks clean.",
    )


def validate_report(report: MustelReport) -> List[str]:
    """
    Validate a MustelReport for schema compliance.

    Returns a list of validation error strings.
    Empty list = valid.
    """
    errors: List[str] = []

    if not report.mustel_version:
        errors.append("mustel_version is required")
    if report.schema_version != 1:
        errors.append(f"schema_version must be 1, got {report.schema_version}")
    if not report.scanned_at:
        errors.append("scanned_at is required")
    if not report.project_root:
        errors.append("project_root is required")
    if report.files_scanned < 0:
        errors.append("files_scanned must be >= 0")
    if report.scan_duration_ms < 0:
        errors.append("scan_duration_ms must be >= 0")

    valid_severities = {"error", "warning", "high", "medium", "low", "critical"}
    for issue in report.results.errors + report.results.security + report.results.warnings:
        if issue.severity not in valid_severities:
            errors.append(f"Issue {issue.id} has invalid severity: {issue.severity}")
        if not issue.file:
            errors.append(f"Issue {issue.id} is missing file path")
        if issue.line < 1:
            errors.append(f"Issue {issue.id} has invalid line number: {issue.line}")

    return errors
