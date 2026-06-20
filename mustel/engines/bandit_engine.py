# mustel/engines/bandit_engine.py
"""
bandit engine — security vulnerability detection.

Runs: bandit -r <path> -f json -ll
Parses bandit's JSON output, normalizes to mustel schema dicts.

Filtering:
  - Only HIGH and MEDIUM confidence results (LOW = too many false positives)
  - Maps bandit severity: HIGH→high, MEDIUM→medium, LOW→low
  - Maps bandit confidence to mustel severity for ranking purposes
"""

from __future__ import annotations

import subprocess
import sys
import json
import os
from typing import List, Dict, Any, Optional


# ─────────────────────────────────────────────
#  Severity / confidence mapping
# ─────────────────────────────────────────────

_BANDIT_SEVERITY_MAP: Dict[str, str] = {
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}

# CWE hints extracted from bandit test IDs
# bandit doesn't always include CWE, so we have a small lookup table
_BANDIT_TEST_CWE: Dict[str, str] = {
    "B101": "CWE-703",   # assert_used
    "B102": "CWE-78",    # exec_used
    "B103": "CWE-732",   # setting_permissions
    "B104": "CWE-605",   # hardcoded_bind_all_interfaces
    "B105": "CWE-259",   # hardcoded_password_string
    "B106": "CWE-259",   # hardcoded_password_funcarg
    "B107": "CWE-259",   # hardcoded_password_default
    "B108": "CWE-377",   # probable_insecure_usage_of_temp_file
    "B110": "CWE-391",   # try_except_pass
    "B112": "CWE-391",   # try_except_continue
    "B201": "CWE-94",    # flask_debug_true
    "B202": "CWE-94",    # flask_debug_true (alt)
    "B301": "CWE-502",   # pickle
    "B302": "CWE-502",   # marshal
    "B303": "CWE-327",   # md5/sha1
    "B304": "CWE-327",   # ciphers
    "B305": "CWE-327",   # cipher_modes
    "B306": "CWE-377",   # mktemp_q
    "B307": "CWE-78",    # eval
    "B308": "CWE-79",    # mark_safe
    "B310": "CWE-601",   # urllib_urlopen
    "B311": "CWE-330",   # random (not for security)
    "B312": "CWE-605",   # telnetlib
    "B313": "CWE-611",   # xml
    "B314": "CWE-611",   # xml
    "B315": "CWE-611",   # xml
    "B316": "CWE-611",   # xml
    "B317": "CWE-611",   # xml
    "B318": "CWE-611",   # xml
    "B319": "CWE-611",   # xml
    "B320": "CWE-611",   # xml
    "B321": "CWE-321",   # ftp_lib
    "B322": "CWE-78",    # input (py2)
    "B323": "CWE-295",   # unverified_context
    "B324": "CWE-327",   # hashlib_new_insecure_functions
    "B325": "CWE-377",   # tempnam
    "B401": "CWE-319",   # import_telnetlib
    "B402": "CWE-319",   # import_ftplib
    "B403": "CWE-502",   # import_pickle
    "B404": "CWE-78",    # import_subprocess
    "B405": "CWE-611",   # import_xml_etree
    "B406": "CWE-611",   # import_xml_sax
    "B407": "CWE-611",   # import_xml_expat
    "B408": "CWE-611",   # import_xml_minidom
    "B409": "CWE-611",   # import_xml_pulldom
    "B410": "CWE-611",   # import_lxml
    "B411": "CWE-601",   # import_xmlrpclib
    "B412": "CWE-295",   # import_httpoxy
    "B413": "CWE-327",   # import_pycrypto
    "B501": "CWE-295",   # request_with_no_cert_validation
    "B502": "CWE-326",   # ssl_with_bad_version
    "B503": "CWE-326",   # ssl_with_bad_defaults
    "B504": "CWE-326",   # ssl_with_no_version
    "B505": "CWE-326",   # weak_cryptographic_key
    "B506": "CWE-20",    # yaml_load
    "B507": "CWE-295",   # ssh_no_host_key_verification
    "B601": "CWE-78",    # paramiko_calls
    "B602": "CWE-78",    # subprocess_popen_with_shell_equals_true
    "B603": "CWE-78",    # subprocess_without_shell_equals_true
    "B604": "CWE-78",    # any_other_function_with_shell_equals_true
    "B605": "CWE-78",    # start_process_with_a_shell
    "B606": "CWE-78",    # start_process_with_no_shell
    "B607": "CWE-78",    # start_process_with_partial_path
    "B608": "CWE-89",    # hardcoded_sql_expressions
    "B609": "CWE-78",    # linux_commands_wildcard_injection
    "B610": "CWE-89",    # django_extra_used
    "B611": "CWE-89",    # django_rawsql_used
    "B612": "CWE-78",    # logging_config_insecure_listen
    "B701": "CWE-94",    # jinja2 autoescape false
    "B702": "CWE-94",    # use of mako templates
    "B703": "CWE-94",    # django mark safe
}


_BANDIT_CMD: Optional[List[str]] = None


def _get_bandit_cmd() -> Optional[List[str]]:
    """Get the command to execute Bandit (binary on PATH preferred, fallback to module)."""
    global _BANDIT_CMD
    if _BANDIT_CMD is not None:
        return _BANDIT_CMD

    # Check PATH first
    try:
        result = subprocess.run(
            ["bandit", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            _BANDIT_CMD = ["bandit"]
            return _BANDIT_CMD
    except Exception:
        pass

    # Check python module fallback
    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            _BANDIT_CMD = [sys.executable, "-m", "bandit"]
            return _BANDIT_CMD
    except Exception:
        pass

    return None


def _normalize_issue(raw: Dict[str, Any], project_root: str) -> Optional[Dict[str, Any]]:
    """
    Normalize one bandit result to mustel schema format.

    bandit JSON result shape:
    {
        "code": "<surrounding source lines>",
        "col_offset": 4,
        "end_col_offset": 20,
        "filename": "/abs/path/to/file.py",
        "issue_confidence": "HIGH",
        "issue_cwe": {"id": 89, "link": "..."},
        "issue_severity": "HIGH",
        "issue_text": "Possible SQL injection ...",
        "line_number": 47,
        "line_range": [47, 48],
        "more_info": "https://...",
        "test_id": "B608",
        "test_name": "hardcoded_sql_expressions"
    }
    """
    try:
        confidence = raw.get("issue_confidence", "LOW")
        # Skip LOW confidence — too many false positives
        if confidence == "LOW":
            return None

        test_id = raw.get("test_id", "B000")
        rule_name = raw.get("test_name", "unknown")
        abs_file = raw.get("filename", "")
        try:
            rel_file = os.path.relpath(abs_file, project_root)
        except ValueError:
            rel_file = abs_file

        line = raw.get("line_number", 1)
        col = raw.get("col_offset", 0) + 1  # bandit is 0-indexed

        bandit_severity = raw.get("issue_severity", "LOW")
        severity = _BANDIT_SEVERITY_MAP.get(bandit_severity, "low")

        message = raw.get("issue_text", "")

        # CWE: try bandit's own field first, then our lookup table
        cwe_data = raw.get("issue_cwe")
        if cwe_data and isinstance(cwe_data, dict) and cwe_data.get("id"):
            cwe = f"CWE-{cwe_data['id']}"
        else:
            cwe = _BANDIT_TEST_CWE.get(test_id, "")

        return {
            "file": rel_file,
            "line": line,
            "col": col,
            "severity": severity,
            "category": "security",
            "rule": f"{test_id}:{rule_name}",
            "message": message,
            "engine": "bandit",
            "module_context": "",
            "cwe": cwe,
            "fix_available": False,
        }
    except Exception:
        return None


def run(path: str | List[str], project_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run bandit on a path (file, directory, or list of files) and return normalized security issues.
    """
    if not path:
        return []

    if project_root is None:
        first_path = path[0] if isinstance(path, list) else path
        project_root = first_path if os.path.isdir(first_path) else os.path.dirname(first_path)

    cmd = _get_bandit_cmd()
    if not cmd:
        return []

    paths_to_check = path if isinstance(path, list) else [path]
    is_dir_scan = any(os.path.isdir(p) for p in paths_to_check)

    try:
        result = subprocess.run(
            cmd + (["-r"] if is_dir_scan else []) + paths_to_check + [
                "-f", "json",
                "-ll",         # low severity threshold (include all, filter later)
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # bandit returns non-zero when it finds issues — that's fine
        output = result.stdout.strip()
        if not output:
            return []

        data = json.loads(output)
        raw_results = data.get("results", [])

        issues = []
        for raw in raw_results:
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
