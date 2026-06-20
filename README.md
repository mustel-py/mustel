# mustel (0.3.0)

**The Agent-Native Linter & Guardrail for AI IDEs and Coding Agents.**

mustel is a high-speed, zero-config static analysis and context layer built specifically to make AI coding agents (Cursor, Windsurf, Claude Code, Claude Desktop) cheaper, faster, and hallucination-free. 

By integrating locally into your file save loops and git hooks, mustel gives AI agents deterministic ground truth and API structures in token-optimized formats.

```text
Your Code -> mustel (Dev/Audit) -> Token-Saved JSON/Text -> AI Agent -> Instant Fixes
```

[![PyPI version](https://img.shields.io/pypi/v/mustel.svg)](https://pypi.org/project/mustel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ⚡ Key Innovations in v0.3.0

### 1. Adaptive Execution Modes (Zero CLI Config)
*   **Dev Mode (Default)**: Automatically triggered on editor file saves or MCP reviews. Runs only local checks (Ruff, Oxlint, custom patterns) and skips all network operations/npm registry calls. Latency is **< 30ms** via stat-based file caching (`mtime` + `size`).
*   **Audit Mode**: Triggered automatically in Git hooks (`pre-commit`) or CI pipelines (detecting `CI` or `GITHUB_ACTIONS`). Runs deep security (Bandit) and package vulnerability scans (pip-audit).

### 2. Repository Mapping (`get_code_map` / `mustel map`)
A dedicated tool that serves a compact, token-dense skeleton (classes, method signatures, arguments, and docstrings) of your codebase. Instead of the AI reading raw source code files to understand your repository (which costs 10,000+ tokens), it reads the map once (**saving up to 95% input tokens**).

### 3. Save Loop Guardrails
On file saves, the editor triggers `review_file`. mustel instantly scans the code for syntax or import errors. If found, it appends a high-priority `=== MUSTEL GUARDRAIL ALERT ===` block in the tool output, directing the AI agent to resolve compile/syntax errors in 1 turn before notifying the user.

### 4. Multi-Language & Jupyter Support
*   **JS/TS Support**: Integrated `oxlint` engine for lightning-fast frontend checking.
*   **Jupyter Notebooks (`.ipynb`)**: Extract and parse code cells JSON, running all custom Python patterns against data science notebooks.
*   **Cloud & Data Science Rule Sets**: Added optimized patterns for `pandas`, `numpy`, `streamlit`, `google_cloud`, `azure`, and `boto3`.

### 5. Zero-Config Global IDE Bootstrapping
When first run (or via `mustel bootstrap`), mustel automatically registers its MCP server globally across:
*   **Cursor**: `%USERPROFILE%\.cursor\mcp.json`
*   **Windsurf**: `~/.codeium/windsurf/mcp_config.json`
*   **Claude Code**: `~/.claude.json`
*   **Claude Desktop**: OS-specific AppData configs
It also automatically injects guardrail rules into `.cursorrules` / `.windsurfrules` and installs git pre-commit hooks.

---

## 🚀 Quick Start

### Install

```bash
pip install mustel
```

### Auto-Configure (Bootstrap)

```bash
mustel bootstrap          # Setup current project local rules and git hooks
mustel bootstrap --global # Register MCP server globally across Cursor, Windsurf, Claude
```

### Scan Your Project

```bash
mustel review             # Runs Dev Mode (fast incremental lint)
mustel review --audit     # Force deep security/CVE Audit Mode
mustel review --file x.py # Scan a single file
mustel map                # Print the codebase skeleton mapping (Text)
```

---

## 🛠️ MCP Server Tools

AI IDEs connect via stdio transport using `mustel serve`. The server exposes these tools:

| MCP Tool | Arguments | Output | Description |
| :--- | :--- | :--- | :--- |
| `review` | `path`, `skip_packages`, `compact`, `audit` | Compact JSON | Concurrently scans workspace files. |
| `review_file` | `file_path`, `compact` | JSON + Alert | Local scan for active save loops (triggers guardrails). |
| `get_code_map` | `path` | Tree Text | Compact AST/regex code mapping skeleton. |
| `env` | - | JSON | Current Python environment snapshot. |
| `bootstrap` | `global_install` | Text | Re-configures IDE settings and hooks. |

---

## 📊 Empirical Benchmarks

Tested on real open-source targets (`requests`, `click`, `watchdog`, `bandit`, `mcp`):

*   **Recall**: **100%** on standard vulnerability checks.
*   **Incremental Latency**: **26 - 32 ms** for typical projects; **79 - 114 ms** for repos with 100+ files.
*   **Token Overhead**: Compressed `agent_prompt` summary fits under **191 characters** (under 50 tokens).
*   **Token Reduction**: **34.4% net savings** in AI-agent review workflows (empirical tiktoken measurement).

---

## 📂 Codebase Layout

```text
mustel/
├── mustel/
│   ├── cli.py         # CLI entrypoints (review, serve, bootstrap, map)
│   ├── runner.py      # ThreadPool-parallel orchestrator with caching checks
│   ├── cache.py       # Stat-based (mtime + size) high-speed cache
│   ├── code_map.py    # AST & regex repository map generator
│   ├── normalizer.py  # Deduplicates findings, assigns IDs, generates prompts
│   ├── schema.py      # TypedDict specifications and compact serializers
│   ├── bootstrap.py   # Global IDE config injector & git hook installer
│   └── patterns/      # YAML rules for 22 Python libraries & ipynb extraction
```

---

## 📄 License

MIT License - Copyright (c) 2026 Ameya K, Raunak N. See [LICENSE](LICENSE) for details.