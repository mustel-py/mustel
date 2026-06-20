# mustel/cache.py
"""
mustel cache — lightweight disk-backed caching based on file stats (mtime and size).
Allows skipping linting for unchanged files, keeping review times under 50ms.
"""

from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional


class MustelCache:
    """Lightweight caching layer using file paths, modification times, and sizes."""

    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.cache_dir = os.path.join(self.project_root, ".mustel")
        self.cache_file = os.path.join(self.cache_dir, "cache.json")
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Load cache from disk. Falls back to empty dict on failure or missing file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}
        else:
            self.data = {}

    def save(self):
        """Save current cache to disk. Creates .mustel directory if missing."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def get_cached_findings(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached findings if the file hasn't changed.
        Returns None if file has changed or is not in cache.
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return None

        try:
            stat = os.stat(abs_path)
            mtime = stat.st_mtime
            size = stat.st_size
        except Exception:
            return None

        try:
            rel_path = os.path.relpath(abs_path, self.project_root)
        except ValueError:
            rel_path = abs_path

        entry = self.data.get(rel_path)
        if entry and entry.get("mtime") == mtime and entry.get("size") == size:
            return entry.get("findings")
        return None

    def update_cached_findings(self, file_path: str, findings: List[Dict[str, Any]]):
        """Update cache entry for a file with its current stat and findings."""
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return

        try:
            stat = os.stat(abs_path)
            mtime = stat.st_mtime
            size = stat.st_size
        except Exception:
            return

        try:
            rel_path = os.path.relpath(abs_path, self.project_root)
        except ValueError:
            rel_path = abs_path

        self.data[rel_path] = {
            "mtime": mtime,
            "size": size,
            "findings": findings,
        }
