# benchmarks/projects/project_independent/app_vuln_api.py
"""
INDEPENDENT TEST FILE #2 — API-style application with subtle bugs.

Based on patterns from real Python CVEs and security advisories.
Written WITHOUT consulting mustel's YAML pattern files.

KNOWN VULNERABILITIES (ground truth):
  1. subprocess.Popen with shell=True and user input
  2. Pickle deserialization from uploaded file
  3. eval() on user-supplied expression
  4. requests.post without timeout to external webhook
  5. os.system() with concatenated user input
  6. Insecure temp file creation with predictable name
  7. XML parsing vulnerable to XXE (xml.etree)
  8. JWT token created with algorithm='none'
"""

import os
import sys
import json
import pickle
import tempfile
import subprocess
import xml.etree.ElementTree as ET

import jwt
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

WEBHOOK_URL = "https://hooks.slack.com/services/T00/B00/xxxx"


@app.route("/execute", methods=["POST"])
def execute_command():
    # VULN 1: shell=True with user-controlled command
    cmd = request.json.get("command", "echo ok")
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return jsonify({"stdout": stdout.decode(), "stderr": stderr.decode()})


@app.route("/upload-model", methods=["POST"])
def upload_model():
    # VULN 2: Pickle deserialization from uploaded file
    uploaded = request.files.get("model")
    if not uploaded:
        return jsonify({"error": "no file"}), 400
    model = pickle.load(uploaded.stream)
    return jsonify({"model_type": str(type(model)), "loaded": True})


@app.route("/calculate")
def calculate():
    # VULN 3: eval() on user-supplied math expression
    expr = request.args.get("expr", "1+1")
    try:
        result = eval(expr)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/notify", methods=["POST"])
def notify():
    # VULN 4: requests.post without timeout
    message = request.json.get("message", "")
    payload = {"text": message}
    resp = requests.post(WEBHOOK_URL, json=payload)
    return jsonify({"status": resp.status_code})


@app.route("/disk-usage")
def disk_usage():
    # VULN 5: os.system() with string concatenation
    path = request.args.get("path", "/tmp")
    os.system("du -sh " + path)
    return jsonify({"checked": path})


@app.route("/export")
def export_data():
    # VULN 6: Predictable temp file name
    data = {"users": ["alice", "bob"]}
    tmp_path = os.path.join(tempfile.gettempdir(), "export_data.json")
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    return jsonify({"exported_to": tmp_path})


@app.route("/parse-xml", methods=["POST"])
def parse_xml():
    # VULN 7: XML parsing (potential XXE if lxml or defused not used)
    raw = request.get_data(as_text=True)
    root = ET.fromstring(raw)
    return jsonify({"root_tag": root.tag, "children": len(root)})


@app.route("/issue-token")
def issue_token():
    # VULN 8: JWT with algorithm='none' — signature bypass
    user = request.args.get("user", "guest")
    token = jwt.encode({"sub": user, "role": "admin"}, key="", algorithm="none")
    return jsonify({"token": token})


if __name__ == "__main__":
    app.run(debug=True)
