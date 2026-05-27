# benchmarks/projects/project_backend/app.py
"""
FastAPI application with realistic industry vulnerabilities.

PLANTED ISSUES:
  1. Line ~16 — Hardcoded AWS keys mapping (Boto3 imitation)
  2. Line ~28 — JWT blind decoding without signature verification
  3. Line ~40 — Path traversal via user-supplied filename in os.path.join
  4. Line ~51 — SSRF via proxying generic URLs with requests.get
  5. Line ~65 — Insecure Deserialization via pickle.loads cache poisoning
"""

import os
import pickle
import jwt
import requests
import boto3
from fastapi import FastAPI, HTTPException, Request, Header

app = FastAPI()

# ISSUE 1: Hardcoded infrastructural keys (line 22)
# Simulates lazily leaving service keys in a config dictionary inside code
AWS_CONF = {
    "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
s3 = boto3.client('s3', **AWS_CONF)

@app.middleware("http")
async def verify_token_middleware(request: Request, call_next):
    # Skip middleware for non-auth needed routes for ease of testing
    if request.url.path in ["/public", "/health"]:
        return await call_next(request)
        
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.split(" ")[1]
        try:
            # ISSUE 2: JWT Blind Decoding (line 41)
            # Fails to verify the cryptographic signature of the token
            decoded = jwt.decode(token, options={"verify_signature": False})
            request.state.user = decoded
        except Exception:
            pass
            
    return await call_next(request)

@app.get("/avatars/{filename}")
async def get_avatar(filename: str):
    # ISSUE 3: Path Traversal (line 52)
    # Allows traversing out of the uploads directory (e.g. filename="../../../etc/passwd")
    base_dir = "/var/www/uploads/avatars"
    filepath = os.path.join(base_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Not found")
        
    with open(filepath, "r") as f:
        return {"content": f.read()}

@app.get("/proxy")
async def fetch_external(url: str):
    # ISSUE 4: Server Side Request Forgery (SSRF) (line 64)
    # Passes user-controlled URL directly without domain/protocol validation.
    # Note: Includes timeout properly to not trigger S113 from old benchmark
    try:
        response = requests.get(url, timeout=5)
        return {"status": response.status_code, "data": response.text[:100]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/webhook")
async def receive_webhook(request: Request):
    # ISSUE 5: Insecure Deserialization (line 75)
    # Deserializing completely untrusted data opens remote code execution
    payload = await request.body()
    try:
        data = pickle.loads(payload)
        return {"processed": True, "type": type(data).__name__}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")
