"""Extract security findings from independent test scan."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mustel.runner import run_review

r = run_review(path="benchmarks/projects/project_independent", skip_packages=True)
d = r.to_dict()

print("=" * 80)
print("SECURITY FINDINGS (independent test)")
print("=" * 80)
for i in d["results"]["security"]:
    print(f"  {i['id']:>5} | {i['file']}:{i['line']:<4} | {i['engine']:<16} | {i['rule']:<30} | {i['message'][:60]}")

print(f"\n  Total security: {d['summary']['total_security']}")
print(f"  Total errors:   {d['summary']['total_errors']}")
print(f"  Total warnings: {d['summary']['total_warnings']}")

print("\n" + "=" * 80)
print("ERRORS")
print("=" * 80)
for i in d["results"]["errors"]:
    print(f"  {i['id']:>5} | {i['file']}:{i['line']:<4} | {i['engine']:<16} | {i['rule']:<30} | {i['message'][:60]}")
