# =============================================================================
# 🦦 MUSTEL CHEAT SHEET - All Key Concepts in One File!
# =============================================================================
# Print this, memorize it, or keep it open while coding!
# =============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║  🧠 MUSTEL - CONCEPTS TO ENGRAVE IN YOUR BRAIN                             ║
╚════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│  #1 - FIND CURRENT PYTHON                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import sys                                                                  │
│  sys.executable  → "C:\\Users\\You\\Python313\\python.exe"                    │
│  sys.version     → "3.13.0 (tags/v3.13.0:..."                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #2 - RUN SHELL COMMANDS                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import subprocess                                                           │
│                                                                              │
│  # Capture output (for processing)                                           │
│  output = subprocess.check_output(["cmd", "arg"], text=True)                 │
│                                                                              │
│  # Show output live (for user to see)                                        │
│  subprocess.run(["cmd", "arg"])                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #3 - GET ALL PACKAGES FROM ANY PYTHON                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import json                                                                 │
│  out = subprocess.check_output(                                              │
│      [python_path, "-m", "pip", "list", "--format=json"],                    │
│      text=True                                                               │
│  )                                                                           │
│  packages = json.loads(out)                                                  │
│  # Returns: [{"name": "numpy", "version": "1.24.0"}, ...]                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #4 - FIND ALL PYTHONS ON WINDOWS                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import os                                                                   │
│                                                                              │
│  # Method 1: Check standard install folder                                   │
│  local = os.path.expandvars(r"%LOCALAPPDATA%\\Programs\\Python")              │
│  for folder in os.listdir(local):                                            │
│      exe = os.path.join(local, folder, "python.exe")                         │
│      if os.path.exists(exe): found.add(exe)                                  │
│                                                                              │
│  # Method 2: Use 'where' command                                             │
│  out = subprocess.check_output(["where", "python"], text=True)               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #5 - CHECK IF MODULE CAN BE IMPORTED                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import importlib.util                                                       │
│  exists = importlib.util.find_spec("numpy") is not None                      │
│                                                                              │
│  # Better than try/import because doesn't actually load the module!          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #6 - COMPARE PATHS CORRECTLY                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import os                                                                   │
│  path1_real = os.path.normcase(os.path.realpath(path1))                      │
│  path2_real = os.path.normcase(os.path.realpath(path2))                      │
│  same = (path1_real == path2_real)                                           │
│                                                                              │
│  # realpath = resolve symlinks                                               │
│  # normcase = normalize case on Windows (C:\\ vs c:\\)                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #7 - DICTIONARY COMPREHENSION (SUPER USEFUL!)                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Old way:                                                                  │
│  result = {}                                                                 │
│  for item in data:                                                           │
│      result[item["key"]] = item["value"]                                     │
│                                                                              │
│  # New way (one line!):                                                      │
│  result = {item["key"]: item["value"] for item in data}                      │
│                                                                              │
│  # With filter:                                                              │
│  result = {k: v for k, v in other.items() if k not in current}               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #8 - CLI ARGUMENTS                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  import sys                                                                  │
│  args = sys.argv[1:]  # Skip script name                                     │
│                                                                              │
│  # python script.py all → args = ["all"]                                     │
│  # python script.py check numpy → args = ["check", "numpy"]                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #9 - PACKAGE STRUCTURE                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  mustel/                                                                     │
│  ├── __init__.py      # Makes it a package (can be empty)                    │
│  ├── __main__.py      # Enables: python -m mustel                            │
│  └── main.py          # Your actual code + main() function                   │
│                                                                              │
│  pyproject.toml       # Package configuration                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  #10 - CREATE CLI COMMAND                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # In pyproject.toml:                                                        │
│  [project.scripts]                                                           │
│  mustel = "mustel.main:main"                                                 │
│                                                                              │
│  # After pip install, "mustel" command runs mustel/main.py's main()          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
  THE DIFF LOGIC (The heart of mustel):
═══════════════════════════════════════════════════════════════════════════════

  current_packages = get_packages(sys.executable)
  other_packages = get_packages(other_python_path)
  
  # Packages in OTHER but not in CURRENT:
  missing = {k: v for k, v in other_packages.items() if k not in current_packages}
  
═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(__doc__)
