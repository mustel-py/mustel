# =============================================================================
# 🎮 INTERACTIVE QUIZ - Test Your Mustel Knowledge!
# =============================================================================
# 
# Run this file and answer the questions.
# No reading required - just prove you learned by doing!
# =============================================================================

import sys
import subprocess
import random

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🎮 MUSTEL KNOWLEDGE QUIZ                                                    ║
║  Test yourself! Answer each question.                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

score = 0
total = 0

def ask(question, answer, hint=""):
    global score, total
    total += 1
    print(f"\n❓ Question {total}: {question}")
    if hint:
        print(f"   💡 Hint: {hint}")
    user_answer = input("\n   Your answer: ").strip().lower()
    correct_answers = [a.lower() for a in answer] if isinstance(answer, list) else [answer.lower()]
    
    if user_answer in correct_answers:
        print("   ✅ CORRECT!")
        score += 1
        return True
    else:
        print(f"   ❌ The answer was: {answer if isinstance(answer, str) else answer[0]}")
        return False

def ask_code(question, test_func, hint=""):
    global score, total
    total += 1
    print(f"\n❓ Question {total}: {question}")
    if hint:
        print(f"   💡 Hint: {hint}")
    print("\n   Type your answer (Python code) and press Enter:")
    user_answer = input("   >>> ").strip()
    
    try:
        result = eval(user_answer)
        if test_func(result):
            print("   ✅ CORRECT!")
            score += 1
            return True
        else:
            print(f"   ❌ Got: {result}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# =============================================================================
# QUIZ QUESTIONS
# =============================================================================

print("\n" + "=" * 60)
print("SECTION 1: Basic Concepts")
print("=" * 60)

ask(
    "What variable in 'sys' gives you the current Python's path?",
    ["sys.executable", "executable"],
    "It's sys.____something____"
)

ask(
    "What module do you import to run shell commands?",
    ["subprocess"],
    "sub______"
)

ask(
    "What format does 'pip list' use to give machine-readable output?",
    ["json", "--format=json"],
    "Think: pip list --format=???"
)

print("\n" + "=" * 60)
print("SECTION 2: Code Challenges")
print("=" * 60)

print("\n❓ Challenge: Write code to get the Python version")
print("   Expected result: something like '3.13.0'")
print("   Type your code:")
user_code = input("   >>> ").strip()
try:
    result = eval(user_code)
    if "3." in str(result) or "Python" in str(result):
        print("   ✅ CORRECT!")
        score += 1
    else:
        print(f"   Got: {result}")
        print("   (Try: sys.version.split()[0])")
except Exception as e:
    print(f"   Error: {e}")
    print("   (Try: sys.version.split()[0])")
total += 1

print("\n" + "=" * 60)
print("SECTION 3: Understanding")
print("=" * 60)

ask(
    "What file enables 'python -m package' to work?",
    ["__main__.py", "main"],
    "It starts with double underscores"
)

ask(
    "In pyproject.toml, what section creates CLI commands?",
    ["[project.scripts]", "project.scripts", "scripts"],
    "[project.????]"
)

ask(
    "What function checks if a module exists WITHOUT importing it?",
    ["importlib.util.find_spec", "find_spec"],
    "importlib.util.????_????"
)

# =============================================================================
# RESULTS
# =============================================================================

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

percentage = int(score / total * 100) if total > 0 else 0

print(f"""
   Your Score: {score}/{total} ({percentage}%)
""")

if percentage >= 80:
    print("   🏆 EXCELLENT! You really understand mustel!")
elif percentage >= 60:
    print("   👍 GOOD! Review the lessons once more.")
else:
    print("   📚 Keep practicing! Run the lessons again.")

print("""
   
To improve:
  - Run the lesson files in learn/ folder
  - Read mustel/main.py with fresh eyes
  - Try adding a new command yourself!
""")

# =============================================================================
# BONUS: Practical Test
# =============================================================================

print("=" * 60)
print("BONUS: Live Test")
print("=" * 60)
print()
print("Let's prove you can DO it, not just answer questions!")
print()

input("Press ENTER to run a live test using YOUR code ideas...")

print("""
Write code that:
1. Gets all packages in current Python
2. Counts how many you have
3. Shows the first 3

I'll start the structure, you fill in the blanks:

def get_packages(python_path):
    out = subprocess.check_output(
        [python_path, "-m", "pip", "list", "--format=json"],
        text=True
    )
    import json
    return json.loads(out)
""")

print("\nRunning the solution...")
print()

import json

def get_packages(python_path):
    out = subprocess.check_output(
        [python_path, "-m", "pip", "list", "--format=json"],
        stderr=subprocess.DEVNULL,
        text=True
    )
    return json.loads(out)

packages = get_packages(sys.executable)
print(f"✅ You have {len(packages)} packages!")
print(f"\nFirst 3:")
for pkg in packages[:3]:
    print(f"   {pkg['name']} == {pkg['version']}")

print("""

🎉 If you understood that code, you understand mustel!

Now go read mustel/main.py - you'll understand EVERY LINE!
""")
