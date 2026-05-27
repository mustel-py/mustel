"""Extract security findings from the REAL-WORLD EVFA vulnerable app."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mustel.runner import run_review

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects", "real_world", "evfa")
r = run_review(path=target, skip_packages=True)
d = r.to_dict()

print("=" * 90)
print("  REAL-WORLD SCAN: Extremely Vulnerable Flask App (EVFA)")
print(f"  Source: https://github.com/manuelz120/extremely-vulnerable-flask-app")
print(f"  Files scanned: {d['files_scanned']}")
print(f"  Scan time: {d['scan_duration_ms']}ms")
print("=" * 90)

print(f"\n  SECURITY FINDINGS ({d['summary']['total_security']})")
print(f"  {'-'*85}")
for i in d["results"]["security"]:
    print(f"  {i['id']:>5} | {i['file']:<30} L{i['line']:<4} | {i['engine']:<16} | {i['rule'][:30]:<30} | {i['message'][:50]}")

print(f"\n  ERRORS ({d['summary']['total_errors']})")
print(f"  {'-'*85}")
for i in d["results"]["errors"]:
    print(f"  {i['id']:>5} | {i['file']:<30} L{i['line']:<4} | {i['engine']:<16} | {i['rule'][:30]:<30} | {i['message'][:50]}")

print(f"\n  SUMMARY: {d['summary']['total_security']} security | {d['summary']['total_errors']} errors | {d['summary']['total_warnings']} warnings")
print(f"  AGENT PROMPT ({len(d['agent_prompt'])} chars):")
print(f"  {d['agent_prompt']}")
