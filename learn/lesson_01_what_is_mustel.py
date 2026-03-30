# =============================================================================
# 🦦 LESSON 1: What is Mustel? (Run this file!)
# =============================================================================
# 
# Welcome! You're going to LEARN BY DOING.
# 
# Mustel is a tool that answers one simple question:
# "What Python packages do I have, and in which Python?"
#
# Why does this matter? Let's find out!
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦦 LESSON 1: Why Mustel Exists                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# EXERCISE 1: The Problem Mustel Solves
# ──────────────────────────────────────────────────────────────────────────────
# 
# Imagine this nightmare scenario (it happens ALL THE TIME):
#
#   You type: pip install numpy
#   Then type: python
#   >>> import numpy
#   ❌ ModuleNotFoundError: No module named 'numpy'
#
# HOW?! You just installed it!
#
# The answer: pip installed numpy into a DIFFERENT Python than the one you ran.
#
# Let's prove you have multiple Pythons right now:

import sys
import os

print("=" * 60)
print("👉 EXERCISE 1: Find Your Active Python")
print("=" * 60)
print()
print(f"The Python running THIS file is:")
print(f"   📍 Path:    {sys.executable}")
print(f"   📍 Version: {sys.version.split()[0]}")
print()

# =============================================================================
# 🧠 KEY CONCEPT #1 (ENGRAVE THIS):
# =============================================================================
# 
#   sys.executable → The path to the Python that is CURRENTLY running
#   sys.version    → The version of that Python
#
# This is HOW mustel knows which Python is "current"
# =============================================================================

print("─" * 60)
print("🧠 KEY CONCEPT #1 - MEMORIZE THIS:")
print("─" * 60)
print("""
   sys.executable  →  Path to the Python running right now
   sys.version     →  Version of that Python
   
   Example:
   >>> import sys
   >>> sys.executable
   'C:\\\\Users\\\\You\\\\Python313\\\\python.exe'
""")

input("\n✋ Press ENTER to continue to Exercise 2...")

# EXERCISE 2: There's more than one Python!
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("👉 EXERCISE 2: How Many Pythons Do You Have?")
print("=" * 60)
print()

# Let's search for other Pythons!
local_programs = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python")

found_pythons = []

# Check the common Windows installation location
if os.path.exists(local_programs):
    print(f"🔍 Searching in: {local_programs}")
    print()
    for folder in os.listdir(local_programs):
        exe_path = os.path.join(local_programs, folder, "python.exe")
        if os.path.exists(exe_path):
            found_pythons.append(exe_path)
            current_marker = " ← YOU ARE HERE" if exe_path.lower() == sys.executable.lower() else ""
            print(f"   Found: {exe_path}{current_marker}")

if not found_pythons:
    print("   (No Pythons found in standard location)")

print()
print(f"🎯 Total Pythons found: {len(found_pythons)}")

# =============================================================================
# 🧠 KEY CONCEPT #2 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #2 - MEMORIZE THIS:")
print("─" * 60)
print("""
   On Windows, Python installs to:
   %LOCALAPPDATA%\\Programs\\Python\\
   
   Each version gets its own folder:
   └── Python\\
       ├── Python311\\  (Python 3.11)
       ├── Python312\\  (Python 3.12)
       └── Python313\\  (Python 3.13)
   
   EACH ONE has its OWN packages!
""")

input("\n✋ Press ENTER to continue to Exercise 3...")

# EXERCISE 3: Your first "mustel-like" code
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("👉 EXERCISE 3: Get Packages (Your First Mustel Code!)")
print("=" * 60)
print()
print("We'll use subprocess to run 'pip list --format=json'")
print()

import subprocess
import json

# This is EXACTLY what mustel does internally!
def get_packages(python_path):
    """Get all packages installed in a Python."""
    try:
        result = subprocess.check_output(
            [python_path, "-m", "pip", "list", "--format=json"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        packages = json.loads(result)
        return {pkg["name"].lower(): pkg["version"] for pkg in packages}
    except:
        return {}

print("📦 Getting packages from YOUR current Python...")
print("   (This might take a few seconds...)")
print()

my_packages = get_packages(sys.executable)

print(f"✅ Found {len(my_packages)} packages!")
print()
print("First 10 packages:")
for i, (name, version) in enumerate(sorted(my_packages.items())[:10]):
    print(f"   {name} == {version}")

print("   ...")

# =============================================================================
# 🧠 KEY CONCEPT #3 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #3 - MEMORIZE THIS:")
print("─" * 60)
print("""
   To get packages from ANY Python:
   
   subprocess.check_output(
       [python_path, "-m", "pip", "list", "--format=json"],
       text=True
   )
   
   This runs:  python.exe -m pip list --format=json
   Returns JSON like: [{"name": "numpy", "version": "1.24.0"}, ...]
""")

print()
print("=" * 60)
print("🎉 LESSON 1 COMPLETE!")
print("=" * 60)
print("""
You now understand:
  ✓ Why mustel exists (multiple Pythons = confusion)
  ✓ How to find the current Python (sys.executable)
  ✓ Where Python installs on Windows
  ✓ How to get package lists (subprocess + pip list)

NEXT LESSON: Run lesson_02_*.py to learn how mustel finds ALL Pythons!
""")
