# =============================================================================
# 🦦 LESSON 3: Comparing Packages (The "diff" Command)
# =============================================================================
# 
# Now we learn the COOLEST feature of mustel:
# Finding packages in OTHER Pythons that you DON'T have in your current one!
# =============================================================================

import sys
import os
import subprocess
import json

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦦 LESSON 3: Comparing Packages Across Pythons                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# Helper functions (from previous lessons)
# =============================================================================

def run_cmd(cmd):
    """Run a command and return output, or None if it fails."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except:
        return None

def get_packages(python_path):
    """Get dict of {package_name: version} for a Python installation."""
    out = run_cmd([python_path, "-m", "pip", "list", "--format=json"])
    if not out:
        return {}
    try:
        data = json.loads(out)
        # Return lowercase names for easy comparison
        return {pkg["name"].lower(): pkg["version"] for pkg in data}
    except:
        return {}

def find_all_pythons():
    """Find all Python installations on the system."""
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
# EXERCISE 1: Get packages from current Python
# =============================================================================

print("=" * 60)
print("👉 EXERCISE 1: Get YOUR Packages")
print("=" * 60)
print()

print("Fetching packages from current Python...")
print(f"(Path: {sys.executable})")
print()

current_packages = get_packages(sys.executable)
print(f"✅ Found {len(current_packages)} packages!")
print()
print("Sample packages:")
for name, version in list(sorted(current_packages.items()))[:5]:
    print(f"   {name} == {version}")
print("   ...")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 2: Get packages from ANOTHER Python
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 2: Get ANOTHER Python's Packages")
print("=" * 60)
print()

others = find_all_pythons()

if not others:
    print("⚠️  No other Python installations found.")
    print("   (You only have one Python installed)")
    print()
    print("For this lesson, we'll simulate with your current Python.")
    other_path = sys.executable
    other_packages = current_packages
else:
    other_path = others[0]  # Pick the first "other" Python
    print(f"Getting packages from: {other_path}")
    print()
    other_packages = get_packages(other_path)
    print(f"✅ Found {len(other_packages)} packages in other Python!")

# =============================================================================
# 🧠 KEY CONCEPT #6 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #6 - MEMORIZE THIS:")
print("─" * 60)
print("""
   DICTIONARY COMPREHENSIONS are super useful!

   # This:
   packages = {}
   for pkg in data:
       packages[pkg["name"]] = pkg["version"]
   
   # Becomes this one-liner:
   packages = {pkg["name"]: pkg["version"] for pkg in data}
   
   Mustel uses these everywhere!
""")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 3: THE DIFF - Find missing packages!
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 3: Find Packages You're MISSING")
print("=" * 60)
print()
print("This is the MAGIC of 'mustel diff'!")
print()
print("Question: What packages does the OTHER Python have that YOU don't?")
print()

# THE KEY LOGIC - This is what mustel diff does!
missing = {}
for name, version in other_packages.items():
    if name not in current_packages:
        missing[name] = version

# Even simpler with dict comprehension:
# missing = {k: v for k, v in other_packages.items() if k not in current_packages}

print(f"📦 Packages in OTHER Python but NOT in yours: {len(missing)}")
print()

if missing:
    print("Missing packages:")
    for name, version in list(sorted(missing.items()))[:10]:
        print(f"   {name} == {version}")
    if len(missing) > 10:
        print(f"   ... and {len(missing) - 10} more")
else:
    print("   ✅ You have everything the other Python has!")

# =============================================================================
# 🧠 KEY CONCEPT #7 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #7 - MEMORIZE THIS:")
print("─" * 60)
print("""
   THE DIFF LOGIC:
   
   missing = {k: v for k, v in other.items() if k not in current}
   
   This one line finds ALL packages that exist in "other"
   but DON'T exist in "current"!
   
   This is the HEART of mustel diff.
""")

input("\n✋ Press ENTER to continue to the CHALLENGE...")

# =============================================================================
# 🎮 CHALLENGE: Build the complete diff command!
# =============================================================================

print()
print("=" * 60)
print("🎮 CHALLENGE: Build Your Own 'diff' Command!")
print("=" * 60)
print()

def cmd_diff():
    """Show packages in other Pythons that aren't in current."""
    print("\n🦦 MY DIFF COMMAND\n")
    
    current = sys.executable
    current_packages = get_packages(current)
    others = find_all_pythons()
    
    if not others:
        print("No other Python installations found.")
        return
    
    print(f"Current Python: {current}")
    print(f"Your packages: {len(current_packages)}")
    
    for other in others:
        other_packages = get_packages(other)
        if not other_packages:
            continue
        
        # Find packages in other that aren't in current
        missing = {k: v for k, v in other_packages.items() if k not in current_packages}
        
        # Get version
        out = run_cmd([other, "--version"])
        version = out.strip() if out else other
        
        print(f"\n{version}")
        print(f"  Path: {other}")
        
        if missing:
            print(f"  📦 {len(missing)} unique packages:")
            for name in sorted(missing)[:5]:
                print(f"    {name} == {missing[name]}")
            if len(missing) > 5:
                print(f"    ... and {len(missing) - 5} more")
        else:
            print("  ✅ No unique packages")

# Run it!
cmd_diff()

print()
print("=" * 60)
print("🎉 LESSON 3 COMPLETE!")
print("=" * 60)
print("""
You now understand:
  ✓ How to get packages from ANY Python
  ✓ Dictionary comprehensions
  ✓ The "diff" logic (finding missing packages)
  ✓ How to build a full command

NEXT LESSON: Run lesson_04_*.py to learn about checking & installing!
""")
