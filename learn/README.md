# 🦦 MUSTEL Interactive Learning

Want to understand mustel by **doing**, not just reading? You're in the right place!

## How to Use This

Run each lesson file in order. They're interactive - press ENTER to continue, answer challenges, and learn by building!

```bash
# Run each lesson in order:
python learn/lesson_01_what_is_mustel.py
python learn/lesson_02_finding_pythons.py
python learn/lesson_03_comparing_packages.py
python learn/lesson_04_check_and_install.py
python learn/lesson_05_cli_complete.py
python learn/lesson_06_virtual_environments.py

# Test yourself:
python learn/quiz.py

# Print the cheatsheet:
python learn/cheatsheet.py
```

## What You'll Learn

| Lesson | Topic | Key Concepts |
|--------|-------|--------------|
| 1 | Why Mustel Exists | `sys.executable`, `sys.version`, the multi-Python problem |
| 2 | Finding All Pythons | `subprocess`, `os.path`, finding installations |
| 3 | Comparing Packages | `pip list --format=json`, dict comprehensions, the diff logic |
| 4 | Check & Install | `importlib.util.find_spec`, `subprocess.run()` vs `check_output()` |
| 5 | Building CLI Tools | `sys.argv`, `__main__.py`, `pyproject.toml` scripts |
| 6 | Virtual Environments | `venv`, `pyvenv.cfg`, `sys.prefix` vs `sys.base_prefix`, isolation |

## Key Concepts Cheatsheet

```python
# 1. Current Python
import sys
sys.executable  # Path to Python running now

# 2. Run commands
import subprocess
output = subprocess.check_output([cmd, args], text=True)

# 3. Get packages  
python_path -m pip list --format=json

# 4. Check if importable
import importlib.util
importlib.util.find_spec("module") is not None

# 5. CLI arguments
args = sys.argv[1:]  # Skip script name
```

## After Completing

You'll be able to:
- Read and understand `mustel/main.py` completely
- Add new commands to mustel
- Build your own Python CLI tools

Happy learning! 🦦
