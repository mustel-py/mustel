# mustel

<p align="center">
  <img src="logo.png" width="220" alt="Mustel Logo">
</p>

<p align="center">
  <a href="https://pypi.org/project/mustel/"><img src="https://img.shields.io/pypi/v/mustel.svg" alt="PyPI version"></a>
  <a href="https://pepy.tech/projects/mustel"><img src="https://static.pepy.tech/personalized-badge/mustel?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=BLUE&left_text=downloads" alt="PyPI Downloads"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

Mustel is a lightweight, high-speed static analysis layer that sits between your code and AI coding agents (such as Cursor, Windsurf, or Claude Code). 

### The Problem
When AI agents review or edit a project, they consume thousands of context tokens reading full source files simply to understand how they connect. If the agent introduces syntax errors, it often requires multiple round-trips of copy-pasting terminal tracebacks to fix them.

### The Solution
Mustel runs locally in under 30ms during save loops and git hooks to:
* **Map Codebases**: Exposes a compressed, 1,500-token skeleton (`get_code_map`) of classes, functions, and docstrings so the agent learns your repository structure instantly without opening raw files.
* **Enforce Save Guardrails**: Catches compile and syntax errors on file save, injecting an immediate `=== MUSTEL GUARDRAIL ALERT ===` directly into the agent's tool output to force self-correction before user review.

```text
Your Code -> mustel (Dev/Audit) -> Token-Saved JSON/Text -> AI Agent -> Instant Fixes
```

---

## ⚡ Key Architecture & Design

### 1. Dual-Execution Modes (Zero Configuration)
Mustel switches its execution profile dynamically based on environmental indicators:
*   **Dev Mode (Default)**: Automatically triggered on editor save events and MCP reviews. Runs only local, non-networked checks (Ruff, Oxlint, local pattern files) and leverages a stat-based cache (checking file modification time and size) to keep incremental latency under 30ms.
*   **Audit Mode**: Triggered inside pre-commit hooks or CI/CD pipelines (when `CI`, `GITHUB_ACTIONS`, or `PRE_COMMIT` variables are present). Enables security checks (Bandit) and package dependency audits (pip-audit).

### 2. Repository Mapping (get_code_map)
Exposes codebase mapping tools via the `get_code_map` MCP tool and `mustel map` CLI command. It parses the project structures using AST parsing for Python/Jupyter and regex-based scanning for JS/TS, producing a highly compressed code skeleton (classes, method signatures, arguments, and docstrings) that fits under 1,500 tokens for average repositories, reducing initial context-loading token consumption by up to 95%.

### 3. Save Loop Guardrails
Mustel intercepts file save events via the editor. If syntax, compile, or import errors are found, it inserts a high-priority `=== MUSTEL GUARDRAIL ALERT ===` block in the tool output, directing the AI agent to resolve compiling issues in 1 turn before presenting the changes to the user.

### 4. Language & Environment Support
*   **Javascript & TypeScript**: Integrated `oxlint` engine to provide sub-millisecond JS/TS checks.
*   **Jupyter Notebooks**: Native parser that extracts Python code cells from `.ipynb` JSON models, running all custom rules against notebooks.
*   **Rule Sets**: Local YAML rule matching engine supporting standard libraries and data frameworks (`pandas`, `numpy`, `streamlit`, `google_cloud`, `azure`, and `boto3`).

### 5. Automated IDE Configuration (bootstrap)
Registers Mustel as a global MCP server across active user directories:
*   **Cursor**: `%USERPROFILE%\.cursor\mcp.json` (Windows) / `~/.cursor/mcp.json` (Mac/Linux)
*   **Windsurf**: `~/.codeium/windsurf/mcp_config.json`
*   **Claude Code**: `~/.claude.json`
*   **Claude Desktop**: OS-specific configuration directories

It also automatically appends required instructions to project `.cursorrules` / `.windsurfrules` and configures git pre-commit hooks.

---

## Quick Start

### Install

```bash
pip install mustel
```

### Configure

```bash
# Register MCP server globally across Cursor, Windsurf, and Claude
mustel bootstrap --global

# Configure local rules and install pre-commit hook in the current workspace
mustel bootstrap
```

### CLI Reference

```bash
# Run local incremental review (Dev Mode)
mustel review

# Force deep security and dependency audits (Audit Mode)
mustel review --audit

# Review a single target file
mustel review --file mustel/runner.py

# Print the repository codebase map
mustel map
```

---

## 🛠️ MCP Server Specification

Mustel runs an MCP server over stdio transport via `mustel serve`. The exposed tools are documented below:

| MCP Tool | Arguments | Output Type | Description |
| :--- | :--- | :--- | :--- |
| `review` | `path` (str), `skip_packages` (bool), `compact` (bool), `audit` (bool) | JSON | Concurrently scans files in the workspace. |
| `review_file` | `file_path` (str), `compact` (bool) | JSON + Text | Scans single file on save (triggers guardrails). |
| `get_code_map` | `path` (str) | Text | Returns a compact AST/regex codebase skeleton. |
| `env` | None | JSON | Returns a snapshot of the Python environment. |
| `bootstrap` | `global_install` (bool) | Text | Re-configures IDE settings and hook scripts. |

---

## 📂 Codebase Layout

```text
mustel/
├── mustel/
│   ├── cli.py         # CLI entrypoints (review, serve, bootstrap, map)
│   ├── runner.py      # Parallel execution engine and thread orchestrator
│   ├── cache.py       # Stat-based (mtime + size) file caching layer
│   ├── code_map.py    # AST & regex repository map generator
│   ├── normalizer.py  # Deduplication, formatting, and prompt serializer
│   ├── schema.py      # TypedDict specifications and compact serializers
│   ├── bootstrap.py   # IDE config injector and pre-commit hook installer
│   └── patterns/      # YAML rules and notebook loader
```

---

## 📄 License

MIT License - Copyright (c) 2026 Ameya K, Raunak N. See [LICENSE](LICENSE) for details.