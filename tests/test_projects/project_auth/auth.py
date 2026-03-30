# tests/test_projects/project_auth/auth.py
"""
Intentionally buggy authentication module.
Used to benchmark mustel's precision and recall.

Planted bugs:
  1. SQL injection via string formatting (sqlite3)
  2. MD5 password hashing (hashlib)
  3. Hardcoded secret key (flask)
  4. Missing input validation
"""

import sqlite3
import hashlib
import flask
from flask import Flask, request

app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret-key-do-not-share-123"  # planted: hardcoded secret

DB_PATH = "users.db"


def get_user(username):
    """Get user by username — SQL injection via string formatting."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # PLANTED BUG: SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()


def hash_password(password):
    """Hash a password — using weak MD5 algorithm."""
    # PLANTED BUG: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


@app.route("/login", methods=["POST"])
def login():
    """Login endpoint — no input validation."""
    # PLANTED BUG: no input validation on user-supplied data
    username = request.form.get("username")
    password = request.form.get("password")

    # Direct use of username in SQL query
    user = get_user(username)
    if user and user[2] == hash_password(password):
        return {"status": "ok", "user": username}
    return {"status": "error"}, 401


@app.route("/register", methods=["POST"])
def register():
    """Register endpoint."""
    username = request.form.get("username")
    password = request.form.get("password")
    hashed = hash_password(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # PLANTED BUG: SQL injection in INSERT
    cursor.execute(f"INSERT INTO users VALUES ('{username}', '{hashed}')")
    conn.commit()
    return {"status": "registered"}


if __name__ == "__main__":
    # PLANTED BUG: debug=True in production
    app.run(debug=True)
