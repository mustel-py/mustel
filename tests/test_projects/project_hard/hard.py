import subprocess
import yaml
import sqlite3
import os
import requests

def run_command(cmd, kwargs):
    # Hard Case 1: passing kwargs containing {"shell": True} dynamically
    # Bandit or ruff might miss this, but patterns might catch it if kwargs map to it explicitly
    # But wait, true static analysis won't catch dynamic kwargs unless it's advanced.
    subprocess.run(cmd, **kwargs)

def run_trick():
    # Hard Case 2: A variable named shell=True string
    dummy_str = "shell=True" 
    # Should NOT trigger shell=True because it's a string, not an argument.
    subprocess.Popen(["ls"], stdout=subprocess.PIPE, shell=False)

def db_query(user_input):
    # Hard Case 3: SQL injection using % operator (instead of f-string)
    query = "SELECT * FROM users WHERE username = '%s'" % user_input
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute(query)

def load_data(payload):
    # Hard Case 4: aliased yaml load
    my_load = yaml.load
    return my_load(payload)

def tricky_request():
    # Hard Case 5: Passing timeout dynamically or as None
    # If a variable is passed, does our pattern catch missing timeout?
    timeout_val = None
    return requests.get("https://example.com", timeout=timeout_val)

def dummy_os_system(cmd):
    # Hard Case 6: wrapping os.system
    os.system(cmd)
