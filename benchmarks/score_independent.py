"""
Independent Benchmark Scoring — Maps mustel findings against ground truth.
These test files were NOT designed using mustel's YAML patterns.
"""

# ──────────────────────────────────────────────────────────────
#  GROUND TRUTH: app_vuln_api.py (8 planted vulnerabilities)
# ──────────────────────────────────────────────────────────────
api_ground_truth = {
    "shell_injection":   {"line_range": (38, 42), "caught": True,
        "evidence": "S005/S006 shell=True on line 38/40 (mustel-patterns + bandit)"},
    "pickle_deser":      {"line_range": (48, 52), "caught": True,
        "evidence": "S007 B301:blacklist pickle on line 51 (bandit)"},
    "eval_rce":          {"line_range": (57, 62), "caught": True,
        "evidence": "S008 B307:blacklist eval() on line 60 (bandit)"},
    "requests_no_timeout": {"line_range": (67, 72), "caught": True,
        "evidence": "E002 requests-no-timeout on line 71 (mustel-patterns)"},
    "os_system":         {"line_range": (76, 80), "caught": True,
        "evidence": "S009/S011 os.system on line 77/79 (mustel-patterns + bandit)"},
    "insecure_tmpfile":  {"line_range": (83, 88), "caught": True,
        "evidence": "S010 B108:hardcoded_tmp_directory on line 78 (bandit) — partial: catches tmp dir, not predictable name"},
    "xml_xxe":           {"line_range": (93, 98), "caught": True,
        "evidence": "S012 B314:blacklist xml.etree.ElementTree on line 97 (bandit)"},
    "jwt_alg_none":      {"line_range": (101, 106), "caught": True,
        "evidence": "S013/S014 jwt-algorithm-none on line 103/105 (mustel-patterns)"},
}

# ──────────────────────────────────────────────────────────────
#  GROUND TRUTH: app_vuln_web.py (8 planted vulnerabilities)
# ──────────────────────────────────────────────────────────────
web_ground_truth = {
    "xss_template_string": {"line_range": (43, 47), "caught": False,
        "evidence": "MISSED — render_template_string with f-string is not detected by any engine"},
    "sql_injection_concat": {"line_range": (50, 55), "caught": True,
        "evidence": "S018 S608 SQL injection on line 53 (ruff)"},
    "ssti_template_injection": {"line_range": (60, 63), "caught": False,
        "evidence": "MISSED — render_template_string(user_input) not in any pattern"},
    "open_redirect":     {"line_range": (66, 69), "caught": False,
        "evidence": "MISSED — redirect(user_input) not in any pattern"},
    "debug_mode":        {"line_range": (94, 96), "caught": True,
        "evidence": "S021 B201:flask_debug_true on line 96 (bandit)"},
    "md5_hashing":       {"line_range": (76, 79), "caught": True,
        "evidence": "S019 B324:hashlib MD5 on line 78 (bandit)"},
    "yaml_unsafe_load":  {"line_range": (87, 91), "caught": True,
        "evidence": "S020 B506:yaml_load on line 90 (bandit)"},
    "hardcoded_db_creds": {"line_range": (30, 32), "caught": False,
        "evidence": "MISSED — DATABASE_URL with password not matched by flask-hardcoded-secret-key pattern"},
}

# ──────────────────────────────────────────────────────────────
#  SCORING
# ──────────────────────────────────────────────────────────────
print("=" * 70)
print("  INDEPENDENT BENCHMARK — Recall Scoring (Blind Test)")
print("=" * 70)

for name, gt in [("app_vuln_api.py", api_ground_truth), ("app_vuln_web.py", web_ground_truth)]:
    caught = sum(1 for v in gt.values() if v["caught"])
    total = len(gt)
    recall = caught / total * 100

    print(f"\n  {name}: {caught}/{total} ({recall:.0f}% recall)")
    print(f"  {'-'*65}")
    for vuln_name, info in gt.items():
        status = "[CAUGHT]" if info["caught"] else "[MISSED]"
        print(f"    {status} {vuln_name}")
        print(f"             {info['evidence']}")

# Combined
all_gt = {**api_ground_truth, **web_ground_truth}
total_caught = sum(1 for v in all_gt.values() if v["caught"])
total_vulns = len(all_gt)
overall_recall = total_caught / total_vulns * 100

print(f"\n{'=' * 70}")
print(f"  OVERALL: {total_caught}/{total_vulns} ({overall_recall:.1f}% recall)")
print(f"  MISSED:  {total_vulns - total_caught} vulnerabilities")
print(f"{'=' * 70}")

missed = [k for k, v in all_gt.items() if not v["caught"]]
print(f"\n  Missed vulnerabilities (honest gaps):")
for m in missed:
    print(f"    - {m}: {all_gt[m]['evidence']}")

print(f"\n  WHY these were missed:")
print(f"    - XSS/SSTI via render_template_string: No pattern for Jinja2 template injection")
print(f"    - Open redirect: No pattern for unvalidated redirect()")
print(f"    - Hardcoded DB URL: Pattern only matches SECRET_KEY, not DATABASE_URL")
print(f"\n  These are genuine gaps in mustel's pattern coverage.")
print(f"  Mustel is a 'blind tripwire' — it catches what its rules cover.")
