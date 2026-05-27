# mustel v0.2.0 — Self-Reference Document

> Everything a maintainer needs to understand, extend, and not break mustel.

---

## 1. What mustel Is (One Paragraph)

mustel is a **non-AI, deterministic static analysis layer** designed to be consumed by AI IDEs and coding agents. It wraps three external CLI tools (ruff, bandit, pip-audit) plus its own YAML-based pattern library, merges all their outputs through a normalizer, and emits a single **schema v1 JSON report**. The report always includes an `agent_prompt` field — a pre-written plain English summary that AI agents can read without parsing JSON. mustel exposes itself as a CLI (`mustel review`, `mustel env`, `mustel serve`) and as an MCP server over stdio transport. No API keys. No internet inside mustel itself (pip-audit queries PyPI advisories, but that is pip-audit's concern).

---

## 2. Directory Map

```
mustel 0.2.0/
├── mustel/                        ← git repo root
│   ├── pyproject.toml             ← build config, dependencies, entry points
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── mustel/                    ← THE PYTHON PACKAGE
│   │   ├── __init__.py            ← version, schema_version, public API
│   │   ├── __main__.py            ← `python -m mustel` entry
│   │   ├── cli.py                 ← click CLI (review, env, serve commands)
│   │   ├── runner.py              ← ORCHESTRATOR — calls all engines
│   │   ├── normalizer.py          ← merges engine outputs → MustelReport
│   │   ├── schema.py              ← dataclasses: MustelReport, MustelIssue, etc.
│   │   ├── env.py                 ← `mustel env` — Python env snapshot
│   │   ├── watcher.py             ← `--watch` mode via watchdog
│   │   ├── mcp_server.py          ← MCP stdio server (review, review_file, env tools)
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── ruff_engine.py     ← runs ruff, normalizes output
│   │   │   ├── bandit_engine.py   ← runs bandit, normalizes output
│   │   │   └── pipaudit_engine.py ← runs pip-audit, normalizes output
│   │   └── patterns/
│   │       ├── __init__.py
│   │       ├── loader.py          ← reads all *.yaml, scans Python files
│   │       ├── asyncio.yaml
│   │       ├── boto3.yaml
│   │       ├── cryptography.yaml
│   │       ├── django.yaml
│   │       ├── fastapi.yaml
│   │       ├── flask.yaml
│   │       ├── hashlib.yaml
│   │       ├── json_module.yaml
│   │       ├── jwt.yaml
│   │       ├── logging.yaml
│   │       ├── os.yaml
│   │       ├── paramiko.yaml
│   │       ├── pickle.yaml
│   │       ├── requests.yaml
│   │       ├── socket.yaml
│   │       ├── sqlite3.yaml
│   │       ├── subprocess.yaml
│   │       ├── tempfile.yaml
│   │       ├── threading.yaml
│   │       ├── xml_module.yaml
│   │       └── yaml_module.yaml
│   ├── benchmarks/
│   │   ├── run_benchmark.py       ← accuracy benchmark (recall, FP, scan time)
│   │   ├── results.json           ← historical benchmark runs
│   │   ├── paper.md               ← research/design notes
│   │   ├── claude_prompt.txt      ← prompt used for AI-assisted development
│   │   ├── token_test_prompt.txt  ← token budget experiments
│   │   └── projects/
│   │       ├── project_auth/      ← 5 planted bugs (SQL inj, MD5, secrets…)
│   │       └── project_backend/   ← 5 planted bugs (AWS keys, JWT, SSRF…)
│   ├── tests/
│   │   └── test_projects/
│   │       ├── project_async/     ← async bug fixtures
│   │       ├── project_auth/      ← auth bug fixtures
│   │       ├── project_clean/     ← zero-issue baseline
│   │       ├── project_hard/      ← edge-case bugs
│   │       └── project_scraper/   ← scraper/shell injection fixtures
│   └── docs/
│       ├── index.html
│       ├── docs.html
│       └── mustel.png
```

---

## 3. Data Flow (End to End)

```
User / AI IDE
     │
     ▼
mustel CLI  ──────────── OR ──────────── MCP server (mustel serve)
     │                                         │
     └──────────────┬────────────────────────--┘
                    ▼
              runner.py  run_review(path, single_file, skip_packages)
                    │
          ┌─────────┼─────────┬──────────────┐
          ▼         ▼         ▼              ▼
      ruff_engine bandit_   patterns/     pipaudit_engine
      .run(path)  engine    loader.run    .run()
                  .run(path) (path)       (no path — scans env)
          │         │         │              │
          └─────────┴─────────┘              │
                    ▼                        │
              normalizer.normalize(          │
                ruff_results,               │
                bandit_results,             │
                pattern_results,  ◄─────────┘
                pipaudit_results,
                project_root, …)
                    │
                    ▼
              MustelReport (schema v1 JSON)
```

**Key rules of this flow:**
- Every engine failure is **silently caught** (`try/except: pass`) — one broken engine never crashes the scan.
- `pipaudit_engine.run()` takes **no path** — it always scans the currently active Python environment.
- All paths emitted in issues are **relative to `project_root`**.

---

## 4. The Schema — The Locked Contract

`mustel/schema.py` defines the **single source of truth**. Every piece of the system reads and writes these dataclasses.

```
MustelReport
├── mustel_version: str          ("0.2.0")
├── schema_version: int          (always 1)
├── scanned_at: str              (ISO 8601 UTC)
├── project_root: str            (absolute path)
├── files_scanned: int
├── scan_duration_ms: int
├── results: MustelResults
│   ├── errors: List[MustelIssue]
│   ├── security: List[MustelIssue]
│   ├── warnings: List[MustelIssue]
│   └── packages: List[PackageVulnerability]
├── summary: MustelSummary
│   ├── total_errors / total_security / total_warnings / total_package_vulnerabilities
│   ├── clean: bool
│   └── highest_severity: str
└── agent_prompt: str            (< 200 chars, plain English for AI agents)
```

**MustelIssue fields:**
| Field | Values / Notes |
|---|---|
| `id` | E001, S002, W003 — assigned by normalizer |
| `file` | relative path |
| `line` | 1-indexed |
| `col` | 1-indexed |
| `severity` | `"error"` `"warning"` `"high"` `"medium"` `"low"` `"critical"` |
| `category` | `"bug"` `"security"` `"style"` `"vulnerability"` |
| `rule` | engine rule name, e.g. `"F821"`, `"B608:hardcoded_sql_expressions"` |
| `message` | human-readable |
| `engine` | `"ruff"` `"bandit"` `"mustel-patterns"` |
| `module_context` | which Python module triggered it (patterns only) |
| `cwe` | e.g. `"CWE-89"` or `""` |
| `fix_available` | `True` only for ruff auto-fixable rules |

> [!IMPORTANT]
> **NEVER change schema field names or types without bumping `__schema_version__` in `__init__.py`**. Downstream AI IDEs parse this JSON by field name. A rename is a breaking change.

---

## 5. Engines — How Each Works

### 5.1 ruff_engine (`engines/ruff_engine.py`)

- **Invocation:** `python -m ruff check <path> --output-format=json --exit-zero --select E,F,B,S,ANN,ASYNC,W`
- **Self-installs** ruff if missing (`pip install ruff>=0.4.0 -q`).
- **Severity** is inferred from rule prefix (e.g., `F` → `"error"`, `S` → `"high"`, `ANN` → `"warning"`).
- **Category** similarly inferred: `F/E/B` → `"bug"`, `S` → `"security"`, `ANN/W/C/N/I` → `"style"`.
- **`fix_available`** is `True` when ruff's JSON includes a non-null `fix` field.
- ruff output shape: `{"code", "filename", "location": {"row", "column"}, "message", "fix"}`.

### 5.2 bandit_engine (`engines/bandit_engine.py`)

- **Invocation:** `python -m bandit -r <path> -f json -ll --quiet`
- **Self-installs** bandit if missing.
- **Filters out LOW confidence** results (`issue_confidence == "LOW"` → skip). This is the primary false-positive suppressor.
- **CWE lookup:** Uses `_BANDIT_TEST_CWE` dict (70+ entries). Falls back to bandit's own `issue_cwe` field if populated.
- **Rule format:** `"B608:hardcoded_sql_expressions"` (test_id + test_name joined with colon).
- bandit returns non-zero exit code when it finds issues — this is **expected and handled**.

### 5.3 pipaudit_engine (`engines/pipaudit_engine.py`)

- **Invocation:** `python -m pip_audit --format=json --progress-spinner=off` (falls back to `pip-audit` direct command).
- **Scans the active Python environment** — not the scanned path.
- **Timeout: 180s** (pip-audit downloads advisory DB on first run).
- Severity defaults to `"medium"` (pip-audit rarely provides CVSS scores in its JSON).
- pip-audit output: list of `{"name", "version", "vulns": [{"id", "aliases", "fix_versions", "description"}]}`.
- CVE IDs are extracted from `aliases` list (anything starting with `"CVE-"`).

---

## 6. The Pattern System (`patterns/`)

This is mustel's **most extensible subsystem**. No Python knowledge required to add a pattern.

### How loader.py Works

1. `_load_all_pattern_files()` — globs `*.yaml` in the `patterns/` directory, loads each, flattens all patterns into one list, attaches `_module` key to each.
2. For each `.py` file being scanned: `_get_imported_modules()` extracts all top-level import names.
3. A pattern is only applied if the file actually imports its module. (`module: "*"` matches all files.)
4. Three detection types:

| Type | Implementation | Notes |
|---|---|---|
| `keyword` | `str in line` per line | Fastest, case-sensitive |
| `pattern` | `re.compile(match).search(line)` per line | Full regex |
| `function_call_missing_arg` | Regex finds call site, checks context (line + next 5 lines) for `missing_arg` string | Heuristic, not AST |

### YAML Pattern File Format

```yaml
module: <module_name>          # must match import name exactly
version_min: "3.0"             # informational only, not enforced
patterns:
  - id: "<module>-<description>"   # UNIQUE across all patterns
    severity: "high"               # high | medium | warning | low
    category: "security"           # security | bug | style
    cwe: "CWE-89"                  # optional
    detect:
      type: "keyword"              # keyword | pattern | function_call_missing_arg
      match: "<string or regex>"   # for keyword/pattern
      function: "func.name"        # for function_call_missing_arg (single)
      functions: [...]             # for function_call_missing_arg (list)
      missing_arg: "timeout"       # for function_call_missing_arg
    message: "Explanation + fix."
    docs: "https://..."            # optional
```

> [!TIP]
> Pattern IDs must be globally unique across all YAML files. Convention: `<module>-<short-kebab-description>`. Example: `sqlite3-sql-injection-format`.

### Current Pattern Coverage (22 modules)

`asyncio` · `boto3` · `cryptography` · `django` · `fastapi` · `flask` · `hashlib` · `json_module` · `jwt` · `logging` · `os` · `paramiko` · `pickle` · `requests` · `socket` · `sqlite3` · `subprocess` · `tempfile` · `threading` · `xml_module` · `yaml_module` · `(boto3)`

---

## 7. The Normalizer (`normalizer.py`)

This is the **heart** of mustel. It takes raw dicts from all engines and produces a clean `MustelReport`.

### Pipeline (in order)

1. **Combine:** `all_code_issues = ruff_results + bandit_results + pattern_results`
2. **Deduplicate:** Same `(file, line)` tuple → keep the highest-priority engine's result. Priority: `bandit > mustel-patterns > ruff`.
3. **Categorize:** Each issue → `"error"` / `"security"` / `"warning"` bucket.
   - `category == "security"` OR `severity in ("high", "critical")` → security bucket
   - `severity == "error"` OR `category == "bug"` → error bucket
   - Else → warning bucket
4. **Sort:** Each bucket sorted by `(file, line)`.
5. **Assign IDs:** `E001, E002…`, `S001, S002…`, `W001, W002…`, `P001, P002…`
6. **Calculate summary:** Count totals, compute `highest_severity`, set `clean` flag.
7. **Generate `agent_prompt`:** Compact (<200 chars) plain English. Format: `"mustel found N issues: HighSec:S001,S002 | PkgVuln:P001 | Errs:E001 | Warns:W001. Use IDs to lookup details in JSON."`

### Severity Ranking (for `highest_severity`)
```python
SEVERITY_RANK = {
    "none": 0, "low": 1, "medium": 2, "warning": 2,
    "high": 3, "error": 3, "critical": 4
}
```

---

## 8. CLI (`cli.py`)

Built with **click**. Entry point: `mustel.cli:main` (defined in `pyproject.toml`).

| Command | What it does | Key options |
|---|---|---|
| `mustel review [path]` | Full scan, JSON to stdout | `--file`, `--watch`, `--no-packages`, `--pretty` |
| `mustel env` | Python environment JSON | `--pretty` |
| `mustel serve` | Start MCP server (blocks) | — |

- `--watch` delegates to `watcher.py` → `watchdog` library.
- `--no-packages` sets `skip_packages=True` in `runner.run_review()`.
- If invoked with no subcommand → shows help (not an error).

---

## 9. MCP Server (`mcp_server.py`)

- **Transport:** stdio (stdin/stdout). No network port.
- **Dependency:** `mcp>=1.0.0` package. Lazy-imported inside `start_mcp_server()`.
- **Tools exposed:**

| MCP Tool | Maps to | Notes |
|---|---|---|
| `review` | `runner.run_review(path, skip_packages)` | `path` defaults to `os.getcwd()` |
| `review_file` | `runner.run_review(single_file=…, skip_packages=True)` | packages always skipped for single file |
| `env` | `env.get_env_snapshot()` | Returns Python version, venv, pip info |

- All tool results returned as `TextContent(type="text", text=json_string)`.
- **AI IDE config:**
```json
{
  "mcpServers": {
    "mustel": {
      "command": "mustel",
      "args": ["serve"]
    }
  }
}
```

---

## 10. Watcher (`watcher.py`)

- Uses `watchdog.observers.Observer` + custom `FileSystemEventHandler`.
- Watches for `.py` file modifications and creations only.
- **Debounce: 500ms** — rapid saves don't trigger multiple scans.
- Runs initial scan immediately on start.
- Prints JSON + `---` separator to stdout after each scan.
- Status messages (watching, stopped) go to **stderr** so they don't corrupt JSON stdout.

---

## 11. Environment Detection (`env.py`)

Returns a dict with: `python_version`, `python_path`, `platform`, `platform_version`, `architecture`, `venv` (active, path, base_python), `pip` (version, available).

Used by: `mustel env` CLI command and the MCP `env` tool.

---

## 12. Dependencies

Defined in `pyproject.toml`. All are **hard dependencies** (not optional):

| Package | Min Version | Purpose |
|---|---|---|
| `ruff` | >=0.4.0 | Bug/style engine |
| `bandit` | >=1.7.0 | Security engine |
| `pip-audit` | >=2.6.0 | CVE engine |
| `watchdog` | >=3.0.0 | `--watch` mode |
| `mcp` | >=1.0.0 | MCP server protocol |
| `pyyaml` | >=6.0 | YAML pattern loading |
| `click` | >=8.0.0 | CLI framework |

- **Python requirement:** `>=3.8`
- **Build system:** hatchling (`[build-system]` in pyproject.toml)
- ruff and bandit are also **auto-installed** by their engines if missing at runtime.

---

## 13. How Files Are Connected (Import Graph)

```
__main__.py
    └── cli.py
            ├── runner.py
            │       ├── schema.py
            │       ├── normalizer.py
            │       │       └── schema.py
            │       ├── engines/ruff_engine.py
            │       ├── engines/bandit_engine.py
            │       ├── engines/pipaudit_engine.py
            │       └── patterns/loader.py (imports yaml)
            ├── watcher.py
            │       └── runner.py (lazy import)
            ├── mcp_server.py
            │       ├── runner.py (lazy import)
            │       └── env.py (lazy import)
            └── env.py
```

**Important:** `mcp_server.py`, `watcher.py`, and engine imports inside `runner.py` are all inside `try/except` or `if not skip_packages` guards. The package can partially function even if some dependencies are missing.

---

## 14. Version Bump Checklist

When releasing a new version:

1. `mustel/__init__.py` → update `__version__`
2. `pyproject.toml` → update `version`
3. `CHANGELOG.md` → add entry
4. If schema changes → also bump `__schema_version__` in `__init__.py` AND update `schema.py`'s `validate_report()` logic
5. Run benchmarks: `python benchmarks/run_benchmark.py project_auth`
6. Build: `python -m build` → check `dist/`
7. Publish: `python -m twine upload dist/*`

---

## 15. How to Add a New Pattern (Step-by-Step)

1. Create `mustel/patterns/<module_name>.yaml`
2. Set `module:` to the exact Python import name (e.g., `boto3`, not `boto`)
3. Write at least one pattern entry with a **globally unique `id`**
4. Choose detection type: `keyword` for simple strings, `pattern` for regex, `function_call_missing_arg` for missing kwargs
5. Test: `mustel review tests/test_projects/ --no-packages --pretty`
6. Verify no false positives on `tests/test_projects/project_clean/`

---

## 16. How to Add a New Engine

1. Create `mustel/engines/<name>_engine.py`
2. Implement `run(path: str, project_root: Optional[str] = None) -> List[Dict[str, Any]]`
3. Each returned dict **must** have keys: `file, line, col, severity, category, rule, message, engine, module_context, cwe, fix_available`
4. Return `[]` on any error — never raise
5. Add `_ensure_<tool>()` for auto-install if applicable
6. Call it in `runner.py` inside a `try/except` block
7. Pass results to `normalize()` as a new argument (and update normalizer signature)
8. Update `engines/__init__.py` docstring

---

## 17. Benchmark System

**Location:** `benchmarks/run_benchmark.py`

**How it works:**
- Scans `benchmarks/projects/<project_name>/app.py`
- Compares findings against a hardcoded ground truth (`PROJECTS_METADATA`)
- Matches by: (a) line number within range AND (b) keyword in rule/message/cwe

**Pass criteria:**
| Metric | Target |
|---|---|
| Recall | >= 80% |
| False positives | <= 1 |
| Scan time | < 3000ms |
| agent_prompt length | < 200 chars |

**Run:** `python benchmarks/run_benchmark.py project_auth`  
**Projects:** `project_auth` (5 bugs), `project_backend` (5 bugs)

Results are appended to `benchmarks/results.json` (never overwritten).

---

## 18. Critical Rules / Invariants

> [!WARNING]
> **Schema v1 is a public API.** Breaking it breaks every AI IDE integration.

> [!CAUTION]
> **Never raise exceptions from engines.** All engine code must catch all exceptions and return `[]`. One broken engine must not crash a scan.

> [!IMPORTANT]
> **Pattern IDs must be globally unique** across all YAML files. The normalizer and benchmark both use these as identifiers.

> [!NOTE]
> **`agent_prompt` must stay under 200 characters.** This is a hard benchmark target because AI agents have tight context windows and read this field directly.

> [!NOTE]
> **`pipaudit_engine.run()` has no `path` argument.** It always scans the active environment. If you need per-project package scanning in the future, this engine needs a redesign.

---

## 19. Known Limitations

| Limitation | Impact | Workaround |
|---|---|---|
| Pattern detection is line-based (no AST) | `function_call_missing_arg` uses 6-line lookahead heuristic, not true AST parsing | Acceptable FP rate; use bandit for AST-level checks |
| pip-audit scans the active environment, not the project | If project has a separate venv, mustel must be run inside that venv | Document for users |
| Deduplication key is `(file, line)` only | Two different issues on the same line → only one reported | Rare edge case |
| `flask-no-csrf` pattern fires on any `import flask` line | High false positive for Flask apps | Known; the pattern is informational not critical |
| bandit `-ll` flag includes LOW severity; filtered in `_normalize_issue` | Very low-severity bandit issues are fully discarded | Intentional design |

---

## 20. File-by-File Quick Reference

| File | Primary Responsibility | Key Functions |
|---|---|---|
| `__init__.py` | Public API surface, version constants | exports: `run_review`, `MustelReport` |
| `__main__.py` | `python -m mustel` entry point | calls `cli.main()` |
| `cli.py` | Click command definitions | `main()`, `review()`, `env_cmd()`, `serve_cmd()` |
| `runner.py` | Orchestrates all engines | `run_review()` |
| `normalizer.py` | Merges, deduplicates, categorizes, generates report | `normalize()`, `_deduplicate()`, `_categorize_issue()`, `_generate_agent_prompt()` |
| `schema.py` | Dataclass definitions + helpers | `MustelReport`, `MustelIssue`, `PackageVulnerability`, `build_empty_report()`, `validate_report()` |
| `env.py` | Python environment snapshot | `get_env_snapshot()` |
| `watcher.py` | File change detection + debounce | `start_watch()`, `_MustelEventHandler` |
| `mcp_server.py` | MCP stdio server | `start_mcp_server()` |
| `engines/ruff_engine.py` | Wraps ruff CLI | `run()`, `_normalize_issue()`, `_ensure_ruff()` |
| `engines/bandit_engine.py` | Wraps bandit CLI | `run()`, `_normalize_issue()`, `_ensure_bandit()`, `_BANDIT_TEST_CWE` dict |
| `engines/pipaudit_engine.py` | Wraps pip-audit CLI | `run()`, `_normalize_vulnerability()`, `_cvss_to_severity()` |
| `patterns/loader.py` | YAML loading + pattern matching | `run()`, `_scan_file()`, `_load_all_pattern_files()`, `_get_imported_modules()` |
| `patterns/*.yaml` | Detection rules per module | No Python — just YAML |
