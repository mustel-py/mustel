# =============================================================================
# 🦦 LESSON 6: Virtual Environments Made Simple
# =============================================================================
#
# The FINAL piece of the Python environment puzzle!
# After this lesson, you'll never be confused about venvs again.
# =============================================================================

import sys
import os
import platform

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦦 LESSON 6: Virtual Environments Made Simple                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Welcome to the most important lesson for any Python developer!

Virtual environments solve the BIGGEST problem in Python:
  "It works on my machine, but not on yours."

Let's understand them from the ground up.
""")

input("✋ Press ENTER to continue...")

# =============================================================================
# SECTION 1: The Problem
# =============================================================================

print()
print("=" * 60)
print("👉 SECTION 1: The Problem Venvs Solve")
print("=" * 60)
print("""
Imagine you have two projects:

  Project A: Needs numpy version 1.24
  Project B: Needs numpy version 2.0

If you install globally:
  
  pip install numpy==1.24   # Project A works!
  pip install numpy==2.0    # Project A breaks, Project B works!

This is called "DEPENDENCY HELL" 😈

The solution? Give each project its OWN Python installation!
That's what a virtual environment is.
""")

input("✋ Press ENTER to continue...")

# =============================================================================
# SECTION 2: What IS a Virtual Environment?
# =============================================================================

print()
print("=" * 60)
print("👉 SECTION 2: What IS a Virtual Environment?")
print("=" * 60)
print("""
A virtual environment is:

  ┌──────────────────────────────────────────────────────────┐
  │  A COPY of Python that lives INSIDE your project folder │
  └──────────────────────────────────────────────────────────┘

When you create a venv, Python makes a folder like this:

  my_project/
  ├── my_code.py
  ├── .venv/                    ← The virtual environment!
  │   ├── Scripts/              ← (Windows) or bin/ (Mac/Linux)
  │   │   ├── python.exe        ← A copy of Python
  │   │   ├── pip.exe           ← A copy of pip
  │   │   └── activate          ← Script to switch to this Python
  │   └── Lib/site-packages/    ← Packages installed HERE, not globally
  └── ...

When you ACTIVATE this venv:
  - python → uses .venv/Scripts/python.exe
  - pip → installs to .venv/Lib/site-packages
  
Your packages are ISOLATED. Project A can't break Project B!
""")

input("✋ Press ENTER to continue...")

# =============================================================================
# SECTION 3: How to Create a Venv (The Manual Way)
# =============================================================================

print()
print("=" * 60)
print("👉 SECTION 3: Creating a Venv (The Old Way)")
print("=" * 60)
print("""
The built-in way to create a venv:

  python -m venv .venv

This creates a .venv folder in your current directory.

Then you have to ACTIVATE it:

  Windows:     .venv\\Scripts\\activate
  Mac/Linux:   source .venv/bin/activate

When activated, you'll see this in your terminal:

  (.venv) C:\\my_project>

That (.venv) means: "I'm now using the virtual Python"

To deactivate:

  deactivate

That's it! But remembering those commands is annoying...
""")

# Show what the current situation is
print()
print("─" * 60)
print("📍 YOUR CURRENT STATUS:")
print("─" * 60)
print()
print(f"  Python executable: {sys.executable}")
print(f"  sys.prefix:        {sys.prefix}")
print(f"  sys.base_prefix:   {sys.base_prefix}")
print()

if sys.prefix != sys.base_prefix:
    print("  ✅ You ARE in a virtual environment right now!")
    print(f"     Venv path: {sys.prefix}")
else:
    print("  ℹ️  You are NOT in a virtual environment right now.")
    print("     You're using the system/global Python.")

print()
input("✋ Press ENTER to continue...")

# =============================================================================
# 🧠 KEY CONCEPT #14 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #14 - MEMORIZE THIS:")
print("─" * 60)
print("""
   HOW TO CHECK IF YOU'RE IN A VENV:
   
   import sys
   
   if sys.prefix != sys.base_prefix:
       print("In a venv!")
   else:
       print("In global Python")
   
   sys.prefix      = Current Python's location
   sys.base_prefix = Original Python's location
   
   When they differ → you're in a venv!
""")

input("✋ Press ENTER to continue...")

# =============================================================================
# SECTION 4: The Mustel Way
# =============================================================================

print()
print("=" * 60)
print("👉 SECTION 4: The Mustel Way (Easy Mode)")
print("=" * 60)
print("""
mustel makes venvs simpler:

  mustel venv           See status dashboard
  mustel venv new       Create a venv
  mustel venv on        Show activate command
  mustel venv off       Show deactivate command
  mustel venv list      Find ALL venvs on your system
  mustel venv destroy   Delete a venv safely

The magic is in the DASHBOARD. Run `mustel venv` and see:

╭────────────────────────────────────────────────────────────╮
│  🦦 mustel venv                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📍 Folder: C:\\Projects\\my-webapp                          │
│                                                            │
│  Status: ✅ ACTIVE                                         │
│  Path: .venv/                                              │
│  Python: Python 3.13.1                                     │
│  Packages: 24                                              │
│  Size: 156.2 MB                                            │
│                                                            │
│  💡 To deactivate: deactivate                              │
│                                                            │
╰────────────────────────────────────────────────────────────╯

No more guessing! Just run `mustel venv` and see exactly what's going on.
""")

input("✋ Press ENTER to continue...")

# =============================================================================
# SECTION 5: Why Can't Mustel Activate For You?
# =============================================================================

print()
print("=" * 60)
print("👉 SECTION 5: Why Can't Mustel Activate the Venv?")
print("=" * 60)
print("""
You might wonder: "Why doesn't `mustel venv on` just activate it?"

Here's the technical reason:

  ┌────────────────────────────────────────────────────────────┐
  │  A Python program CANNOT modify its parent shell.          │
  │                                                            │
  │  When you run `mustel venv on`, Python starts as a        │
  │  CHILD process. It can't change the PARENT (your shell).  │
  │                                                            │
  │  Only YOU can run the activate command in YOUR shell.     │
  └────────────────────────────────────────────────────────────┘

This is how ALL venv tools work:
  - poetry shell → prints command for you to run
  - pipenv shell → same
  - python -m venv → same

So `mustel venv on` shows you the EXACT command to copy-paste.
It's honest and educational!
""")

# Show what the command would be
print("─" * 60)
print("📋 On YOUR system, the activate command would be:")
print("─" * 60)
print()
if platform.system() == "Windows":
    print("   .venv\\Scripts\\activate")
else:
    print("   source .venv/bin/activate")
print()

input("✋ Press ENTER to continue...")

# =============================================================================
# 🧠 KEY CONCEPT #15 (ENGRAVE THIS):
# =============================================================================
print()
print("─" * 60)
print("🧠 KEY CONCEPT #15 - MEMORIZE THIS:")
print("─" * 60)
print("""
   THE VENV GOLDEN RULE:
   
   ┌─────────────────────────────────────────────────────────┐
   │  Every project gets its OWN .venv folder.              │
   │                                                         │
   │  NEVER share venvs between projects.                   │
   │  NEVER install packages globally (except tools like    │
   │  mustel, pip, etc.)                                    │
   └─────────────────────────────────────────────────────────┘
   
   Your workflow:
   1. Create project folder
   2. cd into it
   3. mustel venv new
   4. Activate the venv
   5. pip install whatever you need
   6. Done! Everything is isolated.
""")

input("✋ Press ENTER to continue...")

# =============================================================================
# SECTION 6: How Venvs Work Under the Hood
# =============================================================================

print()
print("=" * 60)
print("👉 SECTION 6: Under the Hood")
print("=" * 60)
print("""
When you run `python -m venv .venv`, Python:

1. Creates a folder structure:
   .venv/
   ├── pyvenv.cfg        ← Config file (marks this as a venv)
   ├── Scripts/          ← Windows: executables here
   │   ├── python.exe    ← Symlink or copy to real Python
   │   ├── pip.exe
   │   └── activate      ← Shell script to modify PATH
   └── Lib/site-packages/  ← Your packages go here

2. The pyvenv.cfg file contains:
   home = C:\\Python313
   include-system-site-packages = false
   version = 3.13.1

3. When you ACTIVATE:
   - It prepends .venv/Scripts to your PATH
   - So `python` now finds .venv/Scripts/python.exe FIRST
   - That's the whole trick!

Activation is just a PATH change. Deactivation undoes it.
""")

# Let's show the pyvenv.cfg detection
print("─" * 60)
print("🔍 DETECTING VENVS (how mustel does it):")
print("─" * 60)
print()

code = '''
def is_venv_folder(path):
    """Check if a folder is a virtual environment."""
    cfg = os.path.join(path, 'pyvenv.cfg')
    return os.path.exists(cfg)
'''
print(code)
print()
print("The presence of pyvenv.cfg is how we KNOW it's a venv!")
print()

input("✋ Press ENTER to continue...")

# =============================================================================
# HANDS-ON EXERCISE
# =============================================================================

print()
print("=" * 60)
print("🎮 HANDS-ON: Let's Check Your System!")
print("=" * 60)
print()

# Check current directory for venv
cwd = os.getcwd()
venv_names = ['.venv', 'venv', 'env', '.env']
found_venv = None

for name in venv_names:
    path = os.path.join(cwd, name)
    cfg = os.path.join(path, 'pyvenv.cfg')
    if os.path.exists(cfg):
        found_venv = path
        break

print(f"📍 Current folder: {cwd}")
print()

if found_venv:
    print(f"✅ Found a venv: {found_venv}")
    
    # Read the pyvenv.cfg
    cfg_path = os.path.join(found_venv, 'pyvenv.cfg')
    print()
    print("   Contents of pyvenv.cfg:")
    try:
        with open(cfg_path, 'r') as f:
            for line in f:
                print(f"     {line.rstrip()}")
    except:
        print("     (couldn't read)")
else:
    print("ℹ️  No venv in this folder.")
    print()
    print("   To create one:")
    print("     mustel venv new")
    print("   Or:")
    print("     python -m venv .venv")

print()
input("✋ Press ENTER to continue...")

# =============================================================================
# SUMMARY
# =============================================================================

print()
print("=" * 60)
print("🎉 LESSON 6 COMPLETE!")
print("=" * 60)
print("""
CONGRATULATIONS! You now understand virtual environments!

┌────────────────────────────────────────────────────────────────────┐
│  KEY TAKEAWAYS                                                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Venv = isolated Python inside your project folder              │
│                                                                    │
│  2. Create: python -m venv .venv  OR  mustel venv new             │
│                                                                    │
│  3. Activate: .venv\\Scripts\\activate (Windows)                    │
│               source .venv/bin/activate (Mac/Linux)               │
│                                                                    │
│  4. Check if in venv: sys.prefix != sys.base_prefix               │
│                                                                    │
│  5. Detect venv folder: look for pyvenv.cfg                       │
│                                                                    │
│  6. mustel venv = easy dashboard + commands                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

The Golden Rule:
  ONE PROJECT = ONE VENV
  
  Never share venvs. Never install project packages globally.
  
That's it! You're now a venv master! 🦦

Next steps:
  1. Try: mustel venv
  2. Read: mustel/venv.py (you now understand it!)
  3. Practice: create a test project with its own venv
""")
