"""
REAL-WORLD BENCHMARK SCORING — Extremely Vulnerable Flask App (EVFA)

Source: https://github.com/manuelz120/extremely-vulnerable-flask-app
This is a REAL open-source project. Mustel had ZERO influence on its creation.

Known vulnerabilities documented in the project's README and source code:
  1. SQL Injection (account.py:33) — f-string in SQLAlchemy text()
  2. SQL Injection (signup.py:16-17) — f-string in SQLAlchemy text()  
  3. Pickle deserialization from cookie (account.py:118) — loads(b64decode(cookie))
  4. Hardcoded SECRET_KEY (app.py:11) — "super secret key"
  5. SSTI in 404 handler (app.py:31-33) — render_template_string(f"{error}...{request.path}")
  6. SSRF via profile image (utils/profile_image.py:7) — urlopen(user_url)
  7. IDOR in notes (routes/account.py:43-46) — no auth check on user_id
  8. Missing CSRF protection — no Flask-WTF CSRF tokens
  9. Delete without ownership check (routes/notes.py:41-49) — any user can delete any note
"""

ground_truth = {
    "sql_injection_search": {
        "file": "routes/account.py", "line": 33,
        "description": "SQL injection via f-string in SQLAlchemy text()",
        "caught": False,
        "evidence": "MISSED - ruff S608 only caught signup.py:16, not account.py:33 (SQLAlchemy text() not detected)",
    },
    "sql_injection_signup": {
        "file": "routes/signup.py", "line": 16,
        "description": "SQL injection via f-string in SQLAlchemy text()",
        "caught": True,
        "evidence": "S010 - ruff S608 caught SQL injection at signup.py:16",
    },
    "pickle_deserialization_cookie": {
        "file": "routes/account.py", "line": 118,
        "description": "pickle.loads() on user-controlled cookie data",
        "caught": True,
        "evidence": "S004 - bandit B301:blacklist caught pickle at account.py:118",
    },
    "hardcoded_secret_key": {
        "file": "app.py", "line": 11,
        "description": "SECRET_KEY hardcoded as 'super secret key'",
        "caught": True,
        "evidence": "S002 - mustel-patterns flask-hardcoded-secret-key at app.py:11",
    },
    "ssti_404_handler": {
        "file": "app.py", "line": 31,
        "description": "render_template_string with user-controlled request.path",
        "caught": False,
        "evidence": "MISSED - No pattern for render_template_string(f-string). Semantic gap.",
    },
    "ssrf_profile_image": {
        "file": "utils/profile_image.py", "line": 7,
        "description": "urlopen() on user-supplied URL (SSRF)",
        "caught": True,
        "evidence": "S011 - bandit B310:blacklist caught urlopen at profile_image.py:7",
    },
    "idor_notes_access": {
        "file": "routes/account.py", "line": 43,
        "description": "Any user can view any other user's notes by changing user_id",
        "caught": False,
        "evidence": "MISSED - IDOR is a logic bug, not detectable by regex/AST",
    },
    "missing_csrf": {
        "file": "app.py", "line": 6,
        "description": "No CSRF protection on any forms",
        "caught": True,
        "evidence": "S001/S003-S009 - mustel-patterns flask-no-csrf flagged across all route files",
    },
    "insecure_delete_no_owner_check": {
        "file": "routes/notes.py", "line": 41,
        "description": "Any user can delete any note without ownership verification",
        "caught": False,
        "evidence": "MISSED - Authorization logic bugs are not detectable by static pattern matching",
    },
}

# ── SCORING ──
print("=" * 80)
print("  REAL-WORLD BENCHMARK: Extremely Vulnerable Flask App (EVFA)")
print("  Source: https://github.com/manuelz120/extremely-vulnerable-flask-app")
print("  23 Python files | Multi-file architecture | NOT created by mustel team")
print("=" * 80)

caught = sum(1 for v in ground_truth.values() if v["caught"])
total = len(ground_truth)
recall = caught / total * 100

print(f"\n  RECALL: {caught}/{total} ({recall:.1f}%)")
print(f"  {'-'*75}")

for name, info in ground_truth.items():
    status = "[CAUGHT]" if info["caught"] else "[MISSED]"
    print(f"  {status} {name}")
    print(f"           File: {info['file']}:{info['line']}")
    print(f"           {info['evidence']}")
    print()

print(f"{'=' * 80}")
print(f"  CLASSIFICATION OF MISSES")
print(f"{'=' * 80}")
print(f"  Regex-addressable (could add a pattern):")
print(f"    - sql_injection_search: SQLAlchemy text() with f-string (account.py:33)")
print(f"    - ssti_404_handler: render_template_string(f'...') (app.py:31)")
print()
print(f"  Fundamentally undetectable by regex:")
print(f"    - idor_notes_access: Logic bug (missing authorization check)")
print(f"    - insecure_delete: Logic bug (missing ownership verification)")
print()
print(f"  This distinction matters: 2 misses are pattern gaps (fixable),")
print(f"  2 misses are architectural (unfixable without semantic analysis).")
