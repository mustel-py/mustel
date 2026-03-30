# mustel/watcher.py
"""
mustel watcher — file change detection for --watch mode.

Uses watchdog to monitor .py files in a directory.
On change: waits 500ms (debounce), then runs a full review.
Prints new JSON to stdout after each scan.
"""

from __future__ import annotations

import sys
import time
import json
import threading
from typing import Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class _MustelEventHandler(FileSystemEventHandler):
    """Handles file system events and debounces re-scans."""

    def __init__(self, path: str, no_packages: bool = False, debounce_ms: int = 500):
        super().__init__()
        self.path = path
        self.no_packages = no_packages
        self.debounce_ms = debounce_ms
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        src_path = str(event.src_path)
        if not src_path.endswith(".py"):
            return
        self._schedule_scan()

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and str(event.src_path).endswith(".py"):
            self._schedule_scan()

    def _schedule_scan(self):
        """Debounce: cancel pending scan and schedule a new one."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(
                self.debounce_ms / 1000.0,
                self._run_scan,
            )
            self._timer.daemon = True
            self._timer.start()

    def _run_scan(self):
        """Run the review and print JSON to stdout."""
        try:
            from mustel.runner import run_review
            report = run_review(path=self.path, skip_packages=self.no_packages)
            print(report.to_json(indent=2), flush=True)
            print("---", flush=True)  # separator between scans
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


def start_watch(path: str = ".", no_packages: bool = False):
    """
    Start watching a directory for Python file changes.

    Runs until interrupted (Ctrl+C).
    Prints JSON to stdout after each change.
    """
    if not WATCHDOG_AVAILABLE:
        print(
            json.dumps({"error": "watchdog not installed. Run: pip install watchdog"}),
            flush=True,
        )
        sys.exit(1)

    import os
    abs_path = os.path.abspath(path)

    # Run an initial scan immediately
    print(f"[mustel watch] Watching {abs_path} for changes...", file=sys.stderr, flush=True)
    print("[mustel watch] Running initial scan...", file=sys.stderr, flush=True)

    try:
        from mustel.runner import run_review
        report = run_review(path=abs_path, skip_packages=no_packages)
        print(report.to_json(indent=2), flush=True)
        print("---", flush=True)
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)

    # Set up watchdog observer
    handler = _MustelEventHandler(path=abs_path, no_packages=no_packages)
    observer = Observer()
    observer.schedule(handler, abs_path, recursive=True)
    observer.start()

    print("[mustel watch] Watching for changes. Press Ctrl+C to stop.", file=sys.stderr, flush=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[mustel watch] Stopped.", file=sys.stderr, flush=True)

    observer.join()
