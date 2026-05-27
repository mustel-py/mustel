# benchmarks/projects/project_independent/app_vuln_web.py
"""
INDEPENDENT TEST FILE — Based on real CVE patterns from OWASP / NVD.

This file was written to simulate vulnerabilities found in real-world
Python applications WITHOUT consulting mustel's YAML pattern rules.
The goal is to test mustel's detection on code it was NOT tuned for.

Source inspiration: OWASP WebGoat Python, Damn Vulnerable Flask App,
and real CVE reports from PyPI advisory database.

KNOWN VULNERABILITIES (ground truth):
  1. XSS via render_template_string with unsanitized user input
  2. SQL injection via string concatenation in raw query
  3. SSTI (Server-Side Template Injection) via Jinja2
  4. Open redirect via unvalidated redirect URL
  5. Debug mode enabled in production
  6. Weak MD5 hash for password verification
  7. yaml.load without safe loader
  8. Hardcoded database credentials in connection string
"""

import os
import hashlib
import yaml
import sqlite3
from flask import Flask, request, redirect, render_template_string, jsonify

# VULN 8: Hardcoded database credentials
DATABASE_URL = "postgresql://admin:password123@db.production.internal:5432/maindb"

app = Flask(__name__)
app.secret_key = "development-key-not-for-prod"

conn = sqlite3.connect(":memory:", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INTEGER, username TEXT, email TEXT, password TEXT)")
cursor.execute("INSERT INTO users VALUES (1, 'admin', 'admin@test.com', 'hashed_pw')")
conn.commit()


@app.route("/")
def index():
    # VULN 1: XSS via render_template_string
    username = request.args.get("user", "Anonymous")
    return render_template_string(f"<h1>Welcome, {username}</h1>")


@app.route("/search")
def search():
    # VULN 2: SQL injection via string concatenation
    term = request.args.get("q", "")
    query = "SELECT * FROM users WHERE username LIKE '%" + term + "%'"
    cursor.execute(query)
    results = cursor.fetchall()
    return jsonify({"results": results})


@app.route("/profile")
def profile():
    # VULN 3: Server-Side Template Injection
    template = request.args.get("template", "{{user}}")
    return render_template_string(template, user="guest")


@app.route("/redirect")
def open_redirect():
    # VULN 4: Open redirect — no validation on target URL
    next_url = request.args.get("next", "/")
    return redirect(next_url)


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    password = data.get("password", "")
    # VULN 6: MD5 for password hashing
    hashed = hashlib.md5(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE password = ?", (hashed,))
    user = cursor.fetchone()
    if user:
        return jsonify({"status": "ok", "user": user[1]})
    return jsonify({"status": "fail"}), 401


@app.route("/config", methods=["POST"])
def load_config():
    # VULN 7: yaml.load without SafeLoader — arbitrary code execution
    raw = request.get_data(as_text=True)
    config = yaml.load(raw)
    return jsonify({"loaded_keys": list(config.keys()) if config else []})


if __name__ == "__main__":
    # VULN 5: Debug mode enabled
    app.run(host="0.0.0.0", debug=True, port=8080)
