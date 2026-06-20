#!/usr/bin/env python3
"""
benchmarks/run_benchmark.py — Measures mustel's detection accuracy.

Runs mustel review against benchmarks/projects/project_auth and scores
the results against 5 known planted issues.

Metrics:
  - Recall:          How many of the 5 planted issues mustel detected
  - False positives: Issues mustel flagged that are NOT in our planted list
  - Scan time:       How long the scan took (ms)
  - agent_prompt:    The generated prompt text and its character length
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

# Add the project root to sys.path so we can import mustel
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BENCHMARK_DIR)
sys.path.insert(0, PROJECT_ROOT)

from mustel.runner import run_review


# ─────────────────────────────────────────────
#  Planted issues — ground truth
# ─────────────────────────────────────────────
# Each planted issue is identified by a keyword pattern that should
# appear in mustel's message or rule field, plus an approximate line range.

PROJECTS_METADATA = {
    "project_auth": {
        "planted_issues": [
            {
                "id": "hardcoded_secret",
                "description": "Hardcoded SECRET_KEY",
                "line_range": (15, 25),
                "keywords": ["hardcod", "secret", "password", "credential"],
            },
            {
                "id": "sql_injection",
                "description": "SQL injection via string formatting",
                "line_range": (30, 42),
                "keywords": ["sql", "injection", "format", "f-string", "S608"],
            },
            {
                "id": "md5_hashing",
                "description": "MD5 password hashing",
                "line_range": (45, 55),
                "keywords": ["md5", "hash", "weak", "insecure", "B303"],
            },
            {
                "id": "no_timeout",
                "description": "requests.get() with no timeout",
                "line_range": (58, 68),
                "keywords": ["timeout", "requests", "S113"],
            },
            {
                "id": "shell_injection",
                "description": "subprocess.run() with shell=True",
                "line_range": (1, 80),
                "keywords": ["shell", "subprocess", "injection", "S602", "S603"],
            },
        ],
        "ignore_rules": {"E402", "E501", "ANN201", "S201", "flask-no-csrf", "flask-debug-true"},
    },
    "project_backend": {
        "planted_issues": [
            {
                "id": "hardcoded_aws",
                "description": "Hardcoded AWS Access Keys",
                "line_range": (20, 30),
                "keywords": ["hardcod", "aws", "boto", "secret", "credential", "B108", "B259"],
            },
            {
                "id": "jwt_verify_false",
                "description": "JWT Blind Decoding (verify=False)",
                "line_range": (38, 48),
                "keywords": ["jwt", "verify", "sign", "insecure", "yaml"],
            },
            {
                "id": "path_traversal",
                "description": "Path Traversal via os.path.join",
                "line_range": (50, 60),
                "keywords": ["path", "traversal", "join", "untrusted"],
            },
            {
                "id": "ssrf_requests",
                "description": "SSRF via proxying generic URLs",
                "line_range": (62, 72),
                "keywords": ["ssrf", "request", "forgery", "external", "variable"],
            },
            {
                "id": "insecure_deserialization",
                "description": "Insecure Deserialization via pickle",
                "line_range": (72, 85),
                "keywords": ["pickle", "deserialization", "untrusted", "S301"],
            },
        ],
        "ignore_rules": {"E402", "E501", "ANN201", "F401", "BLE001", "B904", "W293", "S110"},
    }
}

RESULTS_FILE = os.path.join(BENCHMARK_DIR, "results.json")
TARGET_PATH = os.path.join(BENCHMARK_DIR, "projects", "project_auth")


def _match_issue(finding: dict, planted: dict) -> bool:
    """Check if a mustel finding matches a planted issue."""
    line = finding.get("line", 0)
    lo, hi = planted["line_range"]

    # Line must be in range
    if not (lo <= line <= hi):
        return False

    # At least one keyword must appear in rule, message, or module_context
    text = " ".join([
        finding.get("rule", ""),
        finding.get("message", ""),
        finding.get("module_context", ""),
        finding.get("cwe", ""),
    ]).lower()

    return any(kw.lower() in text for kw in planted["keywords"])


def run_benchmark(project_name: str = "project_auth"):
    """Run the benchmark and return scores."""
    if project_name not in PROJECTS_METADATA:
        print(f"Error: Unknown project '{project_name}'")
        sys.exit(1)
        
    meta = PROJECTS_METADATA[project_name]
    planted_issues = meta["planted_issues"]
    target_path = os.path.join(BENCHMARK_DIR, "projects", project_name)

    print("=" * 60)
    print(f"  MUSTEL BENCHMARK - {project_name}")
    print("=" * 60)

    # Run mustel review
    print(f"\nScanning: {target_path}")
    print("Running mustel review (--no-packages)...\n")

    report = run_review(path=target_path, skip_packages=True)
    report_dict = report.to_dict()

    scan_time_ms = report_dict["scan_duration_ms"]

    # Collect all findings
    all_findings = (
        report_dict["results"]["errors"]
        + report_dict["results"]["security"]
        + report_dict["results"]["warnings"]
    )

    # Filter to only findings in app.py and ignore irrelevant linting/CSRF noise
    ignore_rules = meta["ignore_rules"]
    app_findings = []
    for f in all_findings:
        if "app.py" not in f.get("file", ""):
            continue
        if f.get("rule", "") in ignore_rules:
            continue
        msg = f.get("message", "").lower()
        if "async function" in msg or "raw request" in msg or "unused" in msg:
            continue
        if "try`-`except`-`pass" in msg or "whitespace" in msg:
            continue
        app_findings.append(f)

    # Match planted issues
    detected = []
    matched_finding_ids = set()

    for planted in planted_issues:
        found = False
        for f in app_findings:
            if _match_issue(f, planted):
                found = True
                matched_finding_ids.add(f["id"])
        if found:
            detected.append(planted["id"])

    # Count false positives (findings that don't match any planted issue)
    false_positives = [
        f for f in app_findings
        if f["id"] not in matched_finding_ids
    ]

    recall = len(detected) / len(planted_issues)
    agent_prompt = report_dict.get("agent_prompt", "")

    # Print results
    print("-" * 60)
    print("  RESULTS")
    print("-" * 60)

    print(f"\n  Recall:           {len(detected)}/{len(planted_issues)} ({recall:.0%})")
    for p in planted_issues:
        status = "[PASS]" if p["id"] in detected else "[FAIL]"
        print(f"    {status} {p['description']}")

    print(f"\n  False positives:  {len(false_positives)}")
    for fp in false_positives[:5]:
        print(f"    [WARN] [{fp['id']}] {fp.get('file', '')}:{fp.get('line', '')} - {fp.get('message', '')[:80]}")

    print(f"\n  Scan time:        {scan_time_ms} ms")
    print(f"  agent_prompt len: {len(agent_prompt)} chars")

    # Target evaluation
    print("\n" + "-" * 60)
    print("  TARGET CHECK")
    print("-" * 60)

    targets = [
        ("Recall >= 80%", recall >= 0.80),
        ("False positives <= 1", len(false_positives) <= 1),
        ("Scan time < 3000ms", scan_time_ms < 3000),
        ("agent_prompt < 200 chars", len(agent_prompt) < 200),
    ]

    all_pass = True
    for name, passed in targets:
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"  {icon} {name}")
        if not passed:
            all_pass = False

    if all_pass:
        print("\n  >>> ALL TARGETS MET - benchmark passes!")
    else:
        print("\n  >>> Some targets missed - iteration needed.")

    # Print agent_prompt
    print("\n" + "-" * 60)
    print("  AGENT PROMPT")
    print("-" * 60)
    print(f"\n{agent_prompt}\n")

    # Save to results.json
    result_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project_name,
        "recall_score": recall,
        "recall_detail": detected,
        "missed": [p["id"] for p in planted_issues if p["id"] not in detected],
        "false_positive_count": len(false_positives),
        "false_positives": [
            {"id": fp["id"], "file": fp.get("file", ""), "line": fp.get("line", 0), "message": fp.get("message", "")[:100]}
            for fp in false_positives
        ],
        "scan_time_ms": scan_time_ms,
        "agent_prompt": agent_prompt,
        "agent_prompt_length": len(agent_prompt),
        "all_targets_met": all_pass,
    }

    # Load existing results
    results = []
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r") as f:
                results = json.load(f)
        except (json.JSONDecodeError, IOError):
            results = []

    results.append(result_entry)

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {RESULTS_FILE}")
    print("=" * 60)

    return result_entry


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "project_auth"
    run_benchmark(proj)
