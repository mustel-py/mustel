# mustel/engines/pipaudit_engine.py
"""
pip-audit engine — package CVE vulnerability detection.

Runs: pip-audit --format=json --progress-spinner=off
Parses output, normalizes to mustel PackageVulnerability dicts.

pip-audit scans the currently active Python environment's installed
packages against the PyPI Advisory Database (OSV-based).
No API key required — queries are made to public OSV/PyPI advisories.
"""

from __future__ import annotations

import subprocess
import sys
import json
from typing import List, Dict, Any, Optional


# ─────────────────────────────────────────────
#  Severity inference
#  pip-audit doesn't always include CVSS severity. We infer from CVSS score
#  if available, otherwise default to "medium".
# ─────────────────────────────────────────────

def _cvss_to_severity(score: Optional[float]) -> str:
    """Map a CVSS v3 base score to mustel severity."""
    if score is None:
        return "medium"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def _is_pipaudit_available() -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        # Try alternate invocation
        try:
            result = subprocess.run(
                ["pip-audit", "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False


def _ensure_pipaudit() -> bool:
    if _is_pipaudit_available():
        return True
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pip-audit>=2.6.0", "-q"],
            capture_output=True, timeout=120
        )
        return _is_pipaudit_available()
    except Exception:
        return False


def _get_pip_audit_command() -> Optional[List[str]]:
    """Return the correct pip-audit command for the current environment."""
    # Try module invocation first
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return [sys.executable, "-m", "pip_audit"]
    except Exception:
        pass
    # Fall back to direct command
    return ["pip-audit"]


def _normalize_vulnerability(
    pkg_name: str,
    installed_version: str,
    vuln: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Normalize one pip-audit vulnerability to mustel schema format.

    pip-audit JSON vulnerability shape (inside each package's "vulns" list):
    {
        "id": "GHSA-xxxx-xxxx-xxxx" | "CVE-2023-xxxxx",
        "fix_versions": ["2.31.0"],
        "aliases": ["CVE-2023-xxxxx"],
        "description": "...",
        "published": "2023-05-22T00:00:00Z"
    }
    """
    try:
        vuln_id = vuln.get("id", "")
        aliases = vuln.get("aliases", [])
        description = vuln.get("description", "")
        fix_versions = vuln.get("fix_versions", [])
        fixed_version = fix_versions[0] if fix_versions else ""

        # Prefer CVE ID if present in aliases
        cve_id = ""
        for alias in aliases:
            if alias.startswith("CVE-"):
                cve_id = alias
                break
        if not cve_id and vuln_id.startswith("CVE-"):
            cve_id = vuln_id

        # Build message
        if cve_id:
            message = (
                f"{pkg_name} {installed_version} has a known vulnerability ({cve_id}). "
                f"Upgrade to {fixed_version}." if fixed_version
                else f"{pkg_name} {installed_version} has a known vulnerability ({cve_id})."
            )
        else:
            message = (
                f"{pkg_name} {installed_version} has a known vulnerability ({vuln_id}). "
                f"Upgrade to {fixed_version}." if fixed_version
                else f"{pkg_name} {installed_version} has a known vulnerability ({vuln_id})."
            )

        return {
            "package": pkg_name,
            "installed_version": installed_version,
            "severity": "medium",  # pip-audit rarely has CVSS; default to medium
            "category": "vulnerability",
            "cve": cve_id or vuln_id,
            "fixed_version": fixed_version,
            "message": message,
            "engine": "pip-audit",
        }
    except Exception:
        return None


def run() -> List[Dict[str, Any]]:
    """
    Run pip-audit on the current environment and return normalized vulnerabilities.

    Returns:
        List of normalized vulnerability dicts (no IDs — assigned by normalizer).
        Returns empty list if pip-audit is unavailable or finds nothing.
    """
    if not _ensure_pipaudit():
        return []

    cmd = _get_pip_audit_command()
    if not cmd:
        return []

    try:
        result = subprocess.run(
            cmd + [
                "--format=json",
                "--progress-spinner=off",
            ],
            capture_output=True,
            text=True,
            timeout=180,   # pip-audit can be slow on first run (db download)
        )

        output = result.stdout.strip()
        if not output:
            return []

        data = json.loads(output)

        # pip-audit JSON format:
        # [
        #   {
        #     "name": "requests",
        #     "version": "2.28.0",
        #     "vulns": [ { "id": "...", ... } ]
        #   },
        #   ...
        # ]
        vulnerabilities = []
        packages = data if isinstance(data, list) else data.get("dependencies", [])

        for pkg_entry in packages:
            pkg_name = pkg_entry.get("name", "")
            installed_version = pkg_entry.get("version", "")
            vulns = pkg_entry.get("vulns", [])

            for vuln in vulns:
                normalized = _normalize_vulnerability(pkg_name, installed_version, vuln)
                if normalized:
                    vulnerabilities.append(normalized)

        return vulnerabilities

    except json.JSONDecodeError:
        return []
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []
