# mustel/engines/__init__.py
"""
mustel analysis engines.

Each engine wraps one external tool and returns a list of
normalized dicts compatible with the mustel schema v1.

Engines:
  ruff_engine    — bug detection (ruff)
  bandit_engine  — security detection (bandit)
  pipaudit_engine — package CVE detection (pip-audit)
  oxlint_engine  — JS/TS bug detection (oxlint)
"""
