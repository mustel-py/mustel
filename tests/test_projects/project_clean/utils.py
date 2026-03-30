# tests/test_projects/project_clean/utils.py
"""
Clean, well-written Python module.
Used to test mustel's false positive rate. This file should produce ZERO issues.
"""

from __future__ import annotations

import hashlib
import logging
import os

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using a strong algorithm."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def safe_join(base: str, *paths: str) -> str:
    """
    Join paths safely, preventing path traversal.
    """
    base_real = os.path.realpath(base)
    joined = os.path.realpath(os.path.join(base, *paths))
    if not joined.startswith(base_real):
        raise ValueError(f"Path traversal detected: {joined}")
    return joined


def read_env(key: str, default: str = "") -> str:
    """Read an environment variable with a fallback."""
    return os.environ.get(key, default)


def get_logger(name: str) -> logging.Logger:
    """Create a properly configured logger."""
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        log.addHandler(handler)
    return log
