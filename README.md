# 🦦 mustel

**Non-AI static analysis layer for AI IDEs and coding agents.**

mustel scans your Python code for bugs, security vulnerabilities, and package CVEs — then feeds the results to your AI IDE as structured JSON. No API keys. No internet required inside mustel. Pure deterministic analysis.

```
Your Code → mustel scans → JSON report → AI IDE reads → AI IDE fixes
```

[![PyPI version](https://img.shields.io/pypi/v/mustel.svg)](https://pypi.org/project/mustel/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Why mustel?

AI coding agents hallucinate bugs that don't exist and miss bugs that do. mustel solves this by giving the agent **ground truth** before it starts coding.

mustel unifies three analysis tools into one machine-readable JSON output:

| Engine | What it catches |
|--------|----------------|
| [ruff](https://github.com/astral-sh/ruff) | Syntax errors, unused imports, common bugs, type issues |
| [bandit](https://github.com/PyCQA/bandit) | Security vulnerabilities (SQL injection, hardcoded passwords, etc.) |
| [pip-audit](https://github.com/pypa/pip-audit) | Known CVEs in installed packages |

Plus **20 module-specific YAML patterns** covering `subprocess`, `requests`, `flask`, `django`, `pickle`, `asyncio`, and more.

### The `agent_prompt` — The Key Innovation

Every mustel report includes a pre-written `agent_prompt` field:

```
"agent_prompt": "mustel found 3 issues. Fix in this order:
PRIORITY 1 — 1 HIGH security issue:
  [S001] app/db.py:112 — SQL injection via string formatting
PRIORITY 2 — 1 error:
  [E001] app/auth.py:47 — undefined variable 'user'
PRIORITY 3 — 1 warning:
  [W001] app/utils.py:23 — unused import"
```

The AI agent reads this one field and knows exactly what to fix and in what order. No JSON parsing needed. No hallucination.

---

## Quick Start

### Install

```bash
pip install mustel
```

### Scan your project

```bash
mustel review                    # scan current directory
mustel review ./src              # scan a specific directory
mustel review --file app.py      # scan one file
mustel review --no-packages      # skip CVE check (faster)
mustel review --watch            # auto-scan on save
```

### Output

mustel outputs JSON conforming to **schema v1**:

```json
{
  "mustel_version": "0.2.0",
  "schema_version": 1,
  "scanned_at": "2026-03-30T20:53:00Z",
  "files_scanned": 14,
  "scan_duration_ms": 340,
  "results": {
    "errors": [...],
    "security": [...],
    "warnings": [...],
    "packages": [...]
  },
  "summary": {
    "total_errors": 1,
    "total_security": 1,
    "total_warnings": 1,
    "clean": false,
    "highest_severity": "high"
  },
  "agent_prompt": "mustel found 3 issues. Fix in this order: ..."
}
```

---

## MCP Server (For AI IDEs)

mustel exposes an MCP server that AI IDEs can connect to automatically:

```bash
mustel serve
```

Add to your AI IDE's MCP configuration:

```json
{
  "mcpServers": {
    "mustel": {
      "command": "mustel",
      "args": ["serve"],
      "description": "Python bug and security detection"
    }
  }
}
```

### MCP Tools

| Tool | Input | Output |
|------|-------|--------|
| `review` | `path` (optional) | Full JSON scan report |
| `review_file` | `file_path` | Single-file scan report |
| `env` | — | Python version, venv status, pip info |
| `check_package` | `package_name` | Availability, version, vulnerability status |

---

## Other Commands

```bash
mustel env                # Python environment info (JSON)
mustel check <package>    # Check if a package is installed (JSON)
mustel install <package>  # Install a package safely
mustel venv               # Virtual environment status (JSON)
mustel venv new           # Create a .venv
```

---

## Benchmark Results

Tested against 4 projects with intentionally planted bugs:

| Project | Planted Bugs | Caught | Recall |
|---------|-------------|--------|--------|
| Auth (SQL injection, MD5, hardcoded secrets) | 5 | 5 | 100% |
| Async (bare except, blocking calls, race conditions) | 4 | 4 | 100% |
| Scraper (shell injection, yaml.load, pickle) | 5 | 5 | 100% |
| Clean (should find nothing) | 0 | 0 | ✅ 0% FP |
| **Total** | **14** | **14** | **100%** |

---

## Module Pattern Coverage (Tier 1)

mustel includes YAML-based pattern files for these 20 modules:

`subprocess` · `requests` · `sqlite3` · `os` · `pickle` · `json` · `hashlib` · `flask` · `django` · `fastapi` · `asyncio` · `logging` · `threading` · `tempfile` · `yaml` · `xml` · `socket` · `paramiko` · `cryptography` · `jwt`

**Adding a new pattern requires zero Python knowledge** — just write a YAML file. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              AI IDE / Coding Agent                │
│       (reads mustel JSON, fixes real issues)      │
└──────────────────┬───────────────────────────────┘
                   │ calls
┌──────────────────▼───────────────────────────────┐
│              mustel MCP Server                    │
│          mustel serve (stdio transport)           │
└──────┬──────────────┬──────────────┬─────────────┘
       │              │              │
┌──────▼────┐  ┌──────▼────┐  ┌─────▼──────┐
│   ruff    │  │  bandit   │  │  pip-audit │
│  (bugs)   │  │(security) │  │   (CVEs)   │
└──────┬────┘  └──────┬────┘  └─────┬──────┘
       │              │              │
┌──────▼──────────────▼──────────────▼─────┐
│          mustel normalizer                │
│   Dedup → Categorize → Assign IDs →      │
│   Generate agent_prompt → Schema v1 JSON │
└──────────────────────────────────────────┘
```

---

## License

MIT License — Copyright (c) 2026 Ameya K, Raunak N

See [LICENSE](LICENSE) for full text.
