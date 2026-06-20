# mustel/__init__.py
"""
mustel v0.3.1 - Non-AI static analysis layer for AI IDEs and coding agents.

Scans Python code for bugs and security issues.
Outputs structured JSON that AI IDEs consume directly.

No API keys. No internet required. Pure deterministic analysis.
"""

__version__ = "0.3.1"
__schema_version__ = 1

from mustel.runner import run_review
from mustel.schema import MustelReport

__all__ = ["__version__", "__schema_version__", "run_review", "MustelReport"]
