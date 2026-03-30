# =============================================================================
# 🦦 LESSON 2: Finding ALL Pythons (The Core Skill!)
# =============================================================================
# 
# This is the MOST IMPORTANT function in mustel.
# Master this, and you understand 50% of the tool.
# =============================================================================

import sys
import os
import subprocess
import platform

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦦 LESSON 2: Finding ALL Python Installations                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# 🧠 THE PLAN (How to find ALL Pythons)
# =============================================================================
# 
# Windows has TWO ways to find Python:
#   1. Check the standard install folder: %LOCALAPPDATA%\Programs\Python
#   2. Ask Windows "where is python?" using the 'where' command
#
# Let's build this step by step!
# =============================================================================

print("=" * 60)
print("👉 EXERCISE 1: Method 1 - Check Standard Install Location")
print("=" * 60)
print()

def run_cmd(cmd):
    """Run a command and return output, or None if it fails."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except:
        return None

# METHOD 1: Check the standard folder
found = set()  # Use a SET to avoid duplicates

local_programs = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python")

print(f"Step 1: Checking {local_programs}")
print()

if os.path.exists(local_programs):
    for folder in os.listdir(local_programs):
        exe = os.path.join(local_programs, folder, "python.exe")
        if os.path.exists(exe):
            found.add(exe)
            print(f"   ✅ Found: {exe}")
else:
    print("   ⚠️  Folder doesn't exist (that's okay)")

print()
print(f"   📊 Found {len(found)} Python(s) so far")

input("\n✋ Press ENTER to continue...")

# METHOD 2: Use the 'where' command
print()
print("=" * 60)
print("👉 EXERCISE 2: Method 2 - Use 'where python' Command")
print("=" * 60)
print()

print("Step 2: Running 'where python' command...")
print()

out = run_cmd(["where", "python"])
if out:
    print("Output from 'where python':")
    for line in out.splitlines():
        print(f"   {line}")
        if line.lower().endswith(".exe"):
            found.add(line.strip())
else:
    print("   (Command returned nothing)")

print()
print(f"📊 Total unique Pythons found: {len(found)}")

# =============================================================================
# 🧠 KEY CONCEPT #4 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #4 - MEMORIZE THIS:")
print("─" * 60)
print("""
   Two ways to find Python on Windows:
   
   1. os.path.exists(r"%LOCALAPPDATA%\\Programs\\Python")
      └── Check each subfolder for python.exe
   
   2. subprocess: ["where", "python"]
      └── Windows will tell you all pythons in PATH
   
   Use a SET to collect them (no duplicates)
""")

input("\n✋ Press ENTER to continue...")

# EXERCISE 3: Put it all together!
print()
print("=" * 60)
print("👉 EXERCISE 3: The Complete find_all_pythons() Function")
print("=" * 60)
print()
print("Now let's write the full function used in mustel:")
print()

def find_all_pythons():
    """Find all Python installations on the system."""
    found = set()
    current = sys.executable  # Remember: this is the Python running now
    
    # Method 1: Check standard folder
    local_programs = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python")
    if os.path.exists(local_programs):
        for folder in os.listdir(local_programs):
            exe = os.path.join(local_programs, folder, "python.exe")
            if os.path.exists(exe):
                found.add(exe)
    
    # Method 2: Use 'where' command
    out = run_cmd(["where", "python"])
    if out:
        for line in out.splitlines():
            if line.lower().endswith(".exe"):
                found.add(line.strip())
    
    # Remove duplicates and current python
    result = []
    current_real = os.path.normcase(os.path.realpath(current))
    seen = set()
    
    for path in found:
        try:
            path_real = os.path.normcase(os.path.realpath(path))
            if path_real == current_real:
                continue  # Skip current python
            if path_real not in seen:
                seen.add(path_real)
                result.append(path)
        except:
            pass
    
    return result

print("Testing our function...")
print()

others = find_all_pythons()
print(f"Current Python: {sys.executable}")
print(f"Other Pythons found: {len(others)}")
for p in others:
    print(f"   {p}")

# =============================================================================
# 🧠 KEY CONCEPT #5 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #5 - MEMORIZE THIS:")
print("─" * 60)
print("""
   To compare paths correctly on Windows:

   os.path.realpath(path)   → Resolve symlinks, get "real" path
   os.path.normcase(path)   → Normalize case (c:\\ vs C:\\)
   
   This prevents counting the same Python twice!
""")

input("\n✋ Press ENTER to continue to the CHALLENGE...")

# =============================================================================
# 🎮 CHALLENGE: Build Your Own Version!
# =============================================================================
print()
print("=" * 60)
print("🎮 CHALLENGE: Get Version of Each Python!")
print("=" * 60)
print("""
Your task: For each Python found, get its version.

HINT: Run this command:
   python.exe --version
   
Returns: "Python 3.13.0"

Fill in the function below and run this file again!
""")

# UNCOMMENT AND COMPLETE THIS:
# def get_python_info(python_path):
#     """Get version info for a Python installation."""
#     # Your code here!
#     # Use run_cmd([python_path, "--version"])
#     pass

# --------------------------------------------------
# Here's the solution (try yourself first!)
# --------------------------------------------------

def get_python_info(python_path):
    """Get version info for a Python installation."""
    out = run_cmd([python_path, "--version"])
    if out:
        return out.strip()  # Remove extra whitespace
    return "Unknown"

print()
print("📊 All Pythons with versions:")
print("-" * 50)

# Current Python
current_version = get_python_info(sys.executable)
print(f"★ {current_version} (current)")
print(f"  {sys.executable}")

# Other Pythons
for path in others:
    version = get_python_info(path)
    print(f"  {version}")
    print(f"  {path}")

print("-" * 50)

print()
print("=" * 60)
print("🎉 LESSON 2 COMPLETE!")
print("=" * 60)
print("""
You now understand:
  ✓ Two methods to find Python on Windows
  ✓ Using subprocess to run commands
  ✓ Using sets to avoid duplicates
  ✓ Normalizing paths for comparison
  ✓ Getting Python version from any installation

NEXT LESSON: Run lesson_03_*.py to learn about comparing packages!
""")
