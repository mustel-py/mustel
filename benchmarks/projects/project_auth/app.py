# benchmarks/projects/project_auth/app.py
"""
A small Flask app with 5 planted security issues.
Used by the mustel benchmark to measure detection recall.

PLANTED ISSUES:
  1. Line ~8  — Hardcoded SECRET_KEY
  2. Line ~20 — SQL injection via string formatting
  3. Line ~35 — MD5 password hashing
  4. Line ~50 — requests.get() with no timeout
  5. Line ~65 — subprocess.run() with shell=True
"""

import hashlib
import subprocess

import requests
from flask import Flask, request, jsonify

# ISSUE 1: Hardcoded secret key (line 20)
SECRET_KEY = "super_secret_key_12345"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Fake in-memory DB connection
import sqlite3
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, password TEXT)")
conn.commit()


@app.route("/user")
def get_user():
    # ISSUE 2: SQL injection via string formatting (line 35)
    name = request.args.get("name", "")
    query = f"SELECT * FROM users WHERE name = '{name}'"
    cursor.execute(query)
    row = cursor.fetchone()
    if row:
        return jsonify({"id": row[0], "name": row[1]})
    return jsonify({"error": "not found"}), 404


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    # ISSUE 3: MD5 password hashing (line 50)
    hashed = hashlib.md5(password.encode()).hexdigest()

    cursor.execute("INSERT INTO users (name, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    return jsonify({"success": True, "user": username})


@app.route("/fetch")
def fetch_url():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "url required"}), 400

    # ISSUE 4: requests.get with no timeout (line 63)
    resp = requests.get(url)
    return jsonify({"status": resp.status_code, "length": len(resp.text)})


@app.route("/run")
def run_command():
    cmd = request.args.get("cmd", "echo hello")

    # ISSUE 5: subprocess.run with shell=True (line 71)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return jsonify({"stdout": result.stdout, "stderr": result.stderr})


if __name__ == "__main__":
    app.run(debug=True)
