# =============================================================================
# 🦦 LESSON 5: Building Your Own CLI Tool (The Final Boss!)
# =============================================================================
# 
# You've learned all the pieces. Now let's put them TOGETHER!
# This is how mustel works as a command-line tool.
# =============================================================================

import sys
import os
import subprocess
import json
import importlib.util

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦦 LESSON 5: Building a Complete CLI Tool                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# EXERCISE 1: Understanding sys.argv
# =============================================================================

print("=" * 60)
print("👉 EXERCISE 1: How Commands Get Arguments")
print("=" * 60)
print()
print("When you type: python my_script.py hello world")
print()
print("Python gives you: sys.argv = ['my_script.py', 'hello', 'world']")
print()
print(f"Right now, sys.argv = {sys.argv}")
print()

# =============================================================================
# 🧠 KEY CONCEPT #10 (ENGRAVE THIS):
# =============================================================================
print("─" * 60)
print("🧠 KEY CONCEPT #10 - MEMORIZE THIS:")
print("─" * 60)
print("""
   sys.argv is a LIST of command-line arguments
   
   sys.argv[0] = the script name
   sys.argv[1:] = arguments after the script name
   
   Example:
   $ python script.py all
   
   sys.argv[0] = 'script.py'
   sys.argv[1] = 'all'
   
   So: args = sys.argv[1:]  # Skip the script name
""")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 2: Building the Main Function
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 2: The Main Function Pattern")
print("=" * 60)
print()
print("Here's the pattern mustel uses:")
print()

code = '''
def main():
    args = sys.argv[1:]  # Get arguments (skip script name)
    
    if not args:
        cmd_list()  # No args = default command
    elif args[0] in ("help", "-h", "--help"):
        cmd_help()
    elif args[0] == "all":
        cmd_all()
    elif args[0] == "diff":
        cmd_diff()
    elif args[0] == "check" and len(args) > 1:
        cmd_check(args[1])
    elif args[0] == "install" and len(args) > 1:
        cmd_install(args[1])
    else:
        print(f"Unknown command: {args[0]}")
        cmd_help()

if __name__ == "__main__":
    main()
'''

print(code)

# =============================================================================
# 🧠 KEY CONCEPT #11 (ENGRAVE THIS):
# =============================================================================
print("─" * 60)
print("🧠 KEY CONCEPT #11 - MEMORIZE THIS:")
print("─" * 60)
print("""
   if __name__ == "__main__":
       main()
   
   This means: "Only run main() if this file is run directly"
   
   NOT when it's imported by another file.
   
   This is the STANDARD way to make a Python file both:
   - Runnable as a script
   - Importable as a module
""")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 3: The __main__.py Magic
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 3: How 'python -m mustel' Works")
print("=" * 60)
print()
print("When you run: python -m mustel")
print()
print("Python looks for: mustel/__main__.py")
print()
print("That file contains:")
print()

mainpy_code = '''
# mustel/__main__.py
from mustel.main import main

if __name__ == "__main__":
    main()
'''

print(mainpy_code)

# =============================================================================
# 🧠 KEY CONCEPT #12 (ENGRAVE THIS):
# =============================================================================
print("─" * 60)
print("🧠 KEY CONCEPT #12 - MEMORIZE THIS:")
print("─" * 60)
print("""
   To make "python -m your_package" work:
   
   your_package/
   ├── __init__.py      # Makes it a package (can be empty)
   ├── __main__.py      # Entry point for -m
   └── main.py          # Your actual code
   
   __main__.py just imports and runs your main function!
""")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# EXERCISE 4: Making "mustel" run directly (pyproject.toml)
# =============================================================================

print()
print("=" * 60)
print("👉 EXERCISE 4: Creating the 'mustel' Command")
print("=" * 60)
print()
print("How can you type just 'mustel' instead of 'python -m mustel'?")
print()
print("In pyproject.toml:")
print()

toml_code = '''
[project.scripts]
mustel = "mustel.main:main"
'''

print(toml_code)
print()
print("This tells pip: 'Create a command called mustel that runs mustel.main.main()'")
print()
print("After 'pip install .' or 'pip install mustel', you can use just 'mustel'!")

# =============================================================================
# 🧠 KEY CONCEPT #13 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #13 - MEMORIZE THIS:")
print("─" * 60)
print("""
   pyproject.toml [project.scripts] section:
   
   [project.scripts]
   command-name = "package.module:function"
   
   This creates a command-line tool!
   
   Example:
   mustel = "mustel.main:main"
   
   Now 'mustel' in terminal runs mustel/main.py's main() function
""")

input("\n✋ Press ENTER to continue...")

# =============================================================================
# 🎮 FINAL CHALLENGE: Build a Mini Tool!
# =============================================================================

print()
print("=" * 60)
print("🎮 FINAL CHALLENGE: Build Your Own Mini Mustel!")
print("=" * 60)
print()
print("Here's a complete, working mini version:")
print()

# --- THE MINI MUSTEL ---

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
        return {pkg["name"].lower(): pkg["version"] for pkg in json.loads(out)}
    except:
        return {}

def mini_list():
    print(f"\n🐍 Python {sys.version.split()[0]}")
    print(f"📍 {sys.executable}\n")
    pkgs = get_packages(sys.executable)
    print(f"📦 {len(pkgs)} packages")

def mini_help():
    print("""
Mini Mustel Commands:
  list   - Show current Python info
  help   - Show this help
""")

def mini_main():
    args = sys.argv[1:]
    if not args or args[0] == "list":
        mini_list()
    elif args[0] == "help":
        mini_help()
    else:
        print(f"Unknown: {args[0]}")
        mini_help()

# Run it!
print("Running mini_main()...")
mini_list()

print()
print("=" * 60)
print("🎉 ALL LESSONS COMPLETE!")
print("=" * 60)
print("""
CONGRATULATIONS! You now understand mustel from the ground up!

┌────────────────────────────────────────────────────────────────────┐
│  KEY CONCEPTS TO REMEMBER                                          │
├────────────────────────────────────────────────────────────────────┤
│  1. sys.executable → Current Python path                           │
│  2. sys.argv → Command-line arguments                              │
│  3. subprocess.check_output() → Capture command output             │
│  4. pip list --format=json → Get all packages as JSON              │
│  5. importlib.util.find_spec() → Check if module importable        │
│  6. os.path.realpath() → Normalize paths for comparison            │
│  7. Dictionary comprehensions → Quick data transformations         │
│  8. __main__.py → Enable 'python -m package'                        │
│  9. pyproject.toml scripts → Create CLI commands                   │
└────────────────────────────────────────────────────────────────────┘

What to do next:
  1. Read mustel/main.py - you now understand EVERY line!
  2. Try adding a new command
  3. Run: mustel --help

You built this understanding by DOING, not just reading. Great job! 🦦
""")
