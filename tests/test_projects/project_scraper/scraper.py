# tests/test_projects/project_scraper/scraper.py
"""
Intentionally buggy web scraper module.
Used to benchmark mustel's precision and recall.

Planted bugs:
  1. subprocess with shell=True
  2. os.system() call
  3. yaml.load() without Loader
  4. pickle.loads() on external data
"""

import subprocess
import os
import yaml
import pickle
import requests


def run_command(user_input):
    """Run a system command — shell injection via shell=True."""
    # PLANTED BUG: shell=True with user input
    result = subprocess.run(f"echo {user_input}", shell=True, capture_output=True, text=True)
    return result.stdout


def clean_files(directory):
    """Clean temporary files — os.system() call."""
    # PLANTED BUG: os.system() is a security risk
    os.system(f"rm -rf {directory}/tmp")


def load_config(config_path):
    """Load configuration from YAML — unsafe yaml.load()."""
    with open(config_path) as f:
        # PLANTED BUG: yaml.load() without Loader can execute arbitrary code
        config = yaml.load(f)
    return config


def restore_session(session_data):
    """Restore a scraping session from pickled data."""
    # PLANTED BUG: pickle.loads() on external data (arbitrary code execution)
    session = pickle.loads(session_data)
    return session


def scrape(url):
    """Scrape a URL — requests without timeout."""
    # PLANTED BUG: no timeout
    response = requests.get(url)
    return response.text


if __name__ == "__main__":
    config = load_config("config.yaml")
    result = run_command(config.get("command", "ls"))
    print(result)
