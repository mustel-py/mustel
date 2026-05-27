"""
Comparison benchmark — runs mustel, standalone bandit, and semgrep
on the same independent test project and compares results.
"""
import subprocess
import sys
import os
import json
import time

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BENCHMARK_DIR, "projects", "project_independent")
sys.path.insert(0, os.path.dirname(BENCHMARK_DIR))


def run_mustel():
    """Run mustel and count security findings."""
    from mustel.runner import run_review
    start = time.monotonic()
    report = run_review(path=TARGET, skip_packages=True)
    elapsed = int((time.monotonic() - start) * 1000)
    d = report.to_dict()
    sec_count = d["summary"]["total_security"]
    err_count = d["summary"]["total_errors"]
    total = sec_count + err_count + d["summary"]["total_warnings"]
    prompt_len = len(d.get("agent_prompt", ""))
    return {
        "tool": "mustel",
        "security_findings": sec_count,
        "error_findings": err_count,
        "total_findings": total,
        "time_ms": elapsed,
        "output_size_chars": len(report.to_json()),
        "agent_prompt_chars": prompt_len,
    }


def run_standalone_bandit():
    """Run bandit directly (without mustel wrapper)."""
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "bandit", "-r", TARGET, "-f", "json", "-ll", "--quiet"],
        capture_output=True, text=True, timeout=120
    )
    elapsed = int((time.monotonic() - start) * 1000)
    try:
        data = json.loads(result.stdout)
        findings = data.get("results", [])
        return {
            "tool": "bandit (standalone)",
            "security_findings": len(findings),
            "error_findings": 0,
            "total_findings": len(findings),
            "time_ms": elapsed,
            "output_size_chars": len(result.stdout),
            "agent_prompt_chars": 0,
        }
    except json.JSONDecodeError:
        return {"tool": "bandit (standalone)", "error": "parse failed", "time_ms": elapsed}


def run_semgrep():
    """Run semgrep with auto config."""
    start = time.monotonic()
    result = subprocess.run(
        ["semgrep", "scan", "--config", "auto", "--json", TARGET],
        capture_output=True, text=True, timeout=180
    )
    elapsed = int((time.monotonic() - start) * 1000)
    try:
        data = json.loads(result.stdout)
        findings = data.get("results", [])
        security = [f for f in findings if "security" in f.get("check_id", "").lower()
                     or "cwe" in json.dumps(f.get("extra", {}).get("metadata", {})).lower()]
        return {
            "tool": "semgrep",
            "security_findings": len(security),
            "error_findings": 0,
            "total_findings": len(findings),
            "time_ms": elapsed,
            "output_size_chars": len(result.stdout),
            "agent_prompt_chars": 0,
        }
    except json.JSONDecodeError:
        return {"tool": "semgrep", "total_findings": "parse_error", "time_ms": elapsed,
                "output_size_chars": len(result.stdout) if result.stdout else 0}


if __name__ == "__main__":
    print("=" * 70)
    print("  COMPARISON BENCHMARK: mustel vs bandit vs semgrep")
    print(f"  Target: {TARGET}")
    print("=" * 70)

    results = []

    print("\n  Running mustel...")
    r1 = run_mustel()
    results.append(r1)
    print(f"    Done: {r1.get('total_findings', '?')} findings in {r1['time_ms']}ms")

    print("  Running standalone bandit...")
    r2 = run_standalone_bandit()
    results.append(r2)
    print(f"    Done: {r2.get('total_findings', '?')} findings in {r2['time_ms']}ms")

    print("  Running semgrep (auto config)...")
    r3 = run_semgrep()
    results.append(r3)
    print(f"    Done: {r3.get('total_findings', '?')} findings in {r3['time_ms']}ms")

    # Print comparison table
    print(f"\n{'=' * 70}")
    print(f"  {'Metric':<30} {'mustel':>12} {'bandit':>12} {'semgrep':>12}")
    print(f"  {'-'*66}")

    for metric in ["security_findings", "total_findings", "time_ms", "output_size_chars", "agent_prompt_chars"]:
        label = metric.replace("_", " ").title()
        vals = []
        for r in results:
            v = r.get(metric, "N/A")
            if isinstance(v, int) and v > 999:
                vals.append(f"{v:,}")
            else:
                vals.append(str(v))
        print(f"  {label:<30} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12}")

    print(f"\n  Key insight: mustel's agent_prompt compresses all findings into")
    print(f"  ~{r1.get('agent_prompt_chars', 0)} chars that an AI agent can read instantly,")
    print(f"  vs {r2.get('output_size_chars', 0):,} chars of raw bandit JSON")
    print(f"  or {r3.get('output_size_chars', 0):,} chars of raw semgrep JSON.")
    print(f"{'=' * 70}")

    # Save results
    out = os.path.join(BENCHMARK_DIR, "token_data", "comparison_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {out}")
