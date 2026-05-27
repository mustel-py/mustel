# Contributing to mustel

Thanks for wanting to contribute! mustel is designed to make contributions easy — especially adding new pattern files.

## Quick Setup

```bash
git clone https://github.com/mustel-py/mustel.git
cd mustel
pip install -e ".[dev]"
pre-commit install
```

## How to Run Tests

```bash
# Run mustel against the benchmark test projects
python run_tests.py

# Test a single project
mustel review tests/test_projects/project_auth --no-packages --pretty
```

## How to Add a New Pattern (No Python Needed!)

This is the **easiest way to contribute** and is tagged `good first issue`.

1. Pick a Python module that isn't covered yet (check `mustel/patterns/`)
2. Create a new YAML file: `mustel/patterns/<module_name>.yaml`
3. Follow this format:

```yaml
module: <module_name>
version_min: "3.0"
patterns:
  - id: "<module>-<short-description>"
    severity: "high"          # high | medium | warning | low
    category: "security"      # security | bug | style
    cwe: "CWE-XXX"            # optional, from https://cwe.mitre.org/
    detect:
      type: "keyword"         # keyword | pattern | function_call_missing_arg
      match: "<string to find>"
    message: "Clear explanation of why this is bad and how to fix it."
    docs: "https://..."        # optional link to docs
```

### Detection Types

| Type | Use When | Example |
|------|----------|---------|
| `keyword` | Simple string match | `match: "shell=True"` |
| `pattern` | Regex needed | `match: "os\\.system\\("` |
| `function_call_missing_arg` | Function called without required arg | `function: "requests.get"`, `missing_arg: "timeout"` |

4. Test it: `mustel review tests/test_projects/ --no-packages --pretty`
5. Submit a PR!

## What a Good PR Looks Like

- **Pattern PRs**: Add one YAML file + test it against a sample. Explain the security/bug risk.
- **Engine PRs**: Target `mustel/engines/`. Include before/after test output.
- **Core PRs**: Discuss in an issue first.

## What is Out of Scope

- Don't add human-only CLI commands (emoji output, interactive prompts)
- Don't add features that require API keys or internet access inside mustel
- Don't change the JSON schema without discussion

## Code Style

- We use ruff for linting (naturally)
- Line length: 88 characters
- Target Python 3.10+

## Questions?

Open an issue with the `needs-discussion` label.
