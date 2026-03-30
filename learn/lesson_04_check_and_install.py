# =============================================================================
# 🦦 LESSON 4: Checking & Installing Packages
# =============================================================================
# 
# Two more cool features:
# - check: Is a package installed? Where?
# - install: Install a package to current Python
# =============================================================================

import sys
import os
import subprocess
import json
import importlib.util

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦦 LESSON 4: Check & Install Commands                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# Helper functions (from previous lessons)
# =============================================================================

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except:
        return None

def get_packages(python_path):
    out = run_cmd([python_path, "-m", "pip", "list", "--format=json"])
    if not out:
        return {}
    try:
        data = json.loads(out)
        return {pkg["name"].lower(): pkg["version"] for pkg in data}
    except:
        return {}

def find_all_pythons():
    found = set()
    current = sys.executable
    local_programs = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python")
    if os.path.exists(local_programs):
        for folder in os.listdir(local_programs):
            exe = os.path.join(local_programs, folder, "python.exe")
            if os.path.exists(exe):
                found.add(exe)
    out = run_cmd(["where", "python"])
    if out:
        for line in out.splitlines():
            if line.lower().endswith(".exe"):
                found.add(line.strip())
    result = []
    current_real = os.path.normcase(os.path.realpath(current))
    seen = set()
    for path in found:
        try:
            path_real = os.path.normcase(os.path.realpath(path))
            if path_real == current_real:
                continue
            if path_real not in seen:
                seen.add(path_real)
                result.append(path)
        except:
            pass
    return result

# =============================================================================
# EXERCISE 1: Check if a module is importable
# =============================================================================

print("=" * 60)
print("👉 EXERCISE 1: Check if a Module is Importable")
print("=" * 60)
print()
print("There are TWO ways to check if you can use a package:")
print()
print("1. try/except import (but this actually loads the module)")
print("2. importlib.util.find_spec() (just checks, doesn't load)")
print()

# THE MUSTEL WAY
def is_importable(name):
    """Check if a module can be imported WITHOUT importing it."""
    return importlib.util.find_spec(name) is not None

# Test it!
test_modules = ["json", "numpy", "requests", "fake_module_xyz"]

print("Testing which modules are importable:")
print()
for mod in test_modules:
    result = is_importable(mod)
    emoji = "✅" if result else "❌"
    print(f"   {emoji} {mod}: {'importable' if result else 'NOT found'}")

# =============================================================================
# 🧠 KEY CONCEPT #8 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #8 - MEMORIZE THIS:")
print("─" * 60)
print("""
   importlib.util.find_spec(name)
   
   → Returns a "spec" object if the module exists
   → Returns None if the module doesn't exist
   
   Better than try/import because:
   - Doesn't execute the module
   - Faster
   - Safer
""")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 2: Build the CHECK command
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 2: Build the 'check' Command")
print("=" * 60)
print()

def cmd_check(package_name):
    """Check if a package exists and where."""
    print(f"\n🦦 CHECK '{package_name}'\n")
    
    current = sys.executable
    
    # First: can we import it in current Python?
    if is_importable(package_name):
        print(f"✅ '{package_name}' is available in current Python!")
        print(f"   You can use: import {package_name}")
        return
    
    print(f"❌ '{package_name}' is NOT in current Python")
    print(f"   ({current})")
    print()
    
    # Search other Pythons
    others = find_all_pythons()
    found_in = []
    
    for other in others:
        packages = get_packages(other)
        if package_name.lower() in packages:
            found_in.append((other, packages[package_name.lower()]))
    
    if found_in:
        print("BUT! Found in these Pythons:")
        for path, version in found_in:
            print(f"   {path} → {version}")
        print()
        print(f"To install in current Python:")
        print(f"   pip install {package_name}")
    else:
        print("Not found in ANY Python installation.")
        print()
        print("To install:")
        print(f"   pip install {package_name}")

# Try it!
print("Let's test the check command:")
print()

# Test with a module you probably have
cmd_check("pip")

print()
print("-" * 40)

# Test with something you probably don't have
cmd_check("cowsay")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 3: Build the INSTALL command
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 3: Understanding the Install Command")
print("=" * 60)
print()
print("The install command is simple - it just runs pip!")
print()

def cmd_install(package_name, dry_run=True):
    """Install a package using pip."""
    print(f"\n🦦 INSTALL '{package_name}'\n")
    
    current = sys.executable
    print(f"Installing to: {current}\n")
    
    # Check if already installed
    packages = get_packages(current)
    if package_name.lower() in packages:
        version = packages[package_name.lower()]
        print(f"⚠️  '{package_name}' is already installed (version {version})")
        return
    
    if dry_run:
        print(f"[DRY RUN] Would run:")
        print(f"   {current} -m pip install {package_name}")
        print()
        print("To actually install, use the real mustel command:")
        print(f"   mustel install {package_name}")
        return
    
    # Actually install (not in this lesson!)
    print(f"⏳ Installing {package_name}...")
    result = subprocess.run(
        [current, "-m", "pip", "install", package_name],
        text=True
    )
    
    if result.returncode == 0:
        print(f"\n✅ Successfully installed {package_name}!")
    else:
        print(f"\n❌ Failed to install {package_name}")

# Demo (dry run only - won't actually install)
cmd_install("cowsay", dry_run=True)

# =============================================================================
# 🧠 KEY CONCEPT #9 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #9 - MEMORIZE THIS:")
print("─" * 60)
print("""
   subprocess.run() vs subprocess.check_output()
   
   check_output(): Captures output, returns string
      → Use when you NEED the output
      → Example: pip list --format=json
   
   run(): Runs command, shows output in terminal
      → Use when user should SEE the output
      → Example: pip install numpy
   
   ┌─────────────────┬────────────────┬─────────────────┐
   │ Function        │ Captures Output│ Live Display    │
   ├─────────────────┼────────────────┼─────────────────┤
   │ check_output()  │ YES            │ NO              │
   │ run()           │ NO             │ YES             │
   └─────────────────┴────────────────┴─────────────────┘
""")

print()
print("=" * 60)
print("🎉 LESSON 4 COMPLETE!")
print("=" * 60)
print("""
You now understand:
  ✓ How to check if a module exists (importlib.util.find_spec)
  ✓ How to search for packages across all Pythons
  ✓ How to install packages programmatically
  ✓ When to use subprocess.run() vs check_output()

NEXT LESSON: Run lesson_05_*.py for the CLI & putting it all together!
""")
