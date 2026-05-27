# Changelog

All notable changes to mustel will be documented in this file.

## [0.2.0] - 2026-03-31

### Complete Architecture Overhaul

mustel v0.2.0 is a ground-up rewrite. The old human-facing CLI tool is now a **machine-facing static analysis layer for AI IDEs**.

### Added
- **JSON-only output** - all commands return structured JSON (schema v1)
- **`mustel review`** - the core command, runs full project scan
- **`mustel review --file <path>`** - single-file scan
- **`mustel review --watch`** - auto-scan on file change (watchdog)
- **`mustel serve`** - MCP server for AI IDE integration (stdio transport)
- **ruff engine** - bug and style detection via ruff
- **bandit engine** - security vulnerability detection via bandit
- **pip-audit engine** - package CVE detection via pip-audit
- **Pattern library** - 20 YAML-based module-specific pattern files:
  `subprocess`, `requests`, `sqlite3`, `os`, `pickle`, `json`, `hashlib`,
  `flask`, `django`, `fastapi`, `asyncio`, `logging`, `threading`, `tempfile`,
  `yaml`, `xml`, `socket`, `paramiko`, `cryptography`, `jwt`
- **Normalizer** - deduplicates, categorizes, assigns IDs, generates `agent_prompt`
- **`agent_prompt` field** - pre-written plain English summary for AI agents
- **`mustel env`** - returns Python environment info as JSON
- **`mustel check <pkg>`** - package availability check as JSON
- **`mustel venv`** / **`mustel venv new`** - venv status and creation
- **Test infrastructure** - 4 benchmark test projects with planted bugs

### Removed
- `mustel clean` - humans clean caches, not IDEs
- `mustel upgrade` / `mustel upgrade --safe` - IDEs don't mass-upgrade
- `mustel diff` - no machine use case
- `mustel updates` - pip already does this
- `mustel venv list` - not useful to an agent
- `mustel venv destroy` - dangerous to automate
- `mustel doctor` - too vague, not actionable
- `mustel all` - replaced by `mustel env`
- All emoji-based human output

### Changed
- Build system: setuptools to hatchling
- Entry point: `mustel.main:main` to `mustel.cli:main`
- CLI framework: argparse to click

### Benchmark
- **Recall: 100%** - caught all 14 planted bugs across 4 test projects
- **False positive rate: 0%** - clean project returned zero issues

---

## [0.1.3] - 2026-03-15

### Initial Release
- Human-facing CLI for Python environment inspection
- Commands: list, all, diff, check, install, updates, upgrade, clean, doctor
- Virtual environment manager (venv, venv new, venv list, venv destroy)
