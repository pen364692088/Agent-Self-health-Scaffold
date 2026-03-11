#!/usr/bin/env python3
"""
Session Continuity Checks Runner

Runs all session continuity tests and generates a report.

Usage:
  python scripts/run_session_continuity_checks.py
  python scripts/run_session_continuity_checks.py --gate
  python scripts/run_session_continuity_checks.py --report
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
REPORT_DIR = WORKSPACE / "artifacts" / "session_continuity" / "v1_1"


def run_pytest(test_path: Path, verbose: bool = True) -> dict:
    """Run pytest and return results."""
    cmd = ["pytest", str(test_path), "-v", "--tb=short"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
            timeout=120
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def run_gate_check(gate: str) -> dict:
    """Run a specific gate check."""
    gates = {
        "A": gate_a_check,
        "B": gate_b_check,
        "C": gate_c_check
    }
    
    if gate not in gates:
        return {"success": False, "error": f"Unknown gate: {gate}"}
    
    return gates[gate]()


def gate_a_check() -> dict:
    """Gate A: Protocol / Document / Schema existence check."""
    required_files = [
        "docs/session_continuity/SESSION_RECOVERY_FLOW.md",
        "docs/session_continuity/STATE_SOURCE_PRIORITY.md",
        "docs/session_continuity/CONFLICT_RESOLUTION_RULES.md",
        "docs/session_continuity/WAL_PROTOCOL.md",
        "docs/session_continuity/STATE_CONCURRENCY_POLICY.md",
        "tools/session-start-recovery",
        "tools/state-write-atomic",
        "tools/state-journal-append",
        "tools/state-lock",
    ]
    
    missing = []
    for f in required_files:
        if not (WORKSPACE / f).exists():
            missing.append(f)
    
    return {
        "success": len(missing) == 0,
        "gate": "A",
        "missing_files": missing,
        "checked": len(required_files),
        "passed": len(required_files) - len(missing)
    }


def gate_b_check() -> dict:
    """Gate B: E2E recovery flow test."""
    # Test recovery flow
    result = subprocess.run(
        [str(WORKSPACE / "tools" / "session-start-recovery"), "--recover", "--json"],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        return {
            "success": False,
            "gate": "B",
            "error": "Recovery command failed"
        }
    
    try:
        data = json.loads(result.stdout)
        if not data.get("recovered"):
            return {
                "success": False,
                "gate": "B",
                "error": "Recovery returned recovered=false"
            }
    except json.JSONDecodeError:
        return {
            "success": False,
            "gate": "B",
            "error": "Invalid JSON output"
        }
    
    return {
        "success": True,
        "gate": "B",
        "message": "E2E recovery flow passed"
    }


def gate_c_check() -> dict:
    """Gate C: Tool chain availability check."""
    tools = [
        str(WORKSPACE / "tools" / "session-start-recovery"),
        "state-write-atomic",
        "state-journal-append",
        "state-lock"
    ]
    
    unavailable = []
    for tool in tools:
        tool_path = WORKSPACE / "tools" / tool
        if not tool_path.exists() or not os.access(tool_path, os.X_OK):
            unavailable.append(tool)
    
    return {
        "success": len(unavailable) == 0,
        "gate": "C",
        "unavailable_tools": unavailable,
        "checked": len(tools),
        "passed": len(tools) - len(unavailable)
    }


def generate_report(results: dict) -> str:
    """Generate a markdown report."""
    lines = [
        "# Session Continuity v1.1 Validation Report",
        "",
        f"**Generated**: {datetime.now().isoformat()}",
        "",
        "## Gate Results",
        "",
    ]
    
    for gate, result in results.get("gates", {}).items():
        status = "PASS" if result.get("success") else "FAIL"
        lines.append(f"### Gate {gate}: {status}")
        
        if result.get("error"):
            lines.append(f"- Error: {result['error']}")
        if result.get("passed"):
            lines.append(f"- Passed: {result['passed']}/{result.get('checked', '?')}")
        if result.get("missing_files"):
            lines.append(f"- Missing: {', '.join(result['missing_files'])}")
        lines.append("")
    
    lines.extend([
        "## Summary",
        "",
        f"- Total Gates: {len(results.get('gates', {}))}",
        f"- Passed: {sum(1 for r in results.get('gates', {}).values() if r.get('success'))}",
        f"- Failed: {sum(1 for r in results.get('gates', {}).values() if not r.get('success'))}",
        ""
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Session Continuity Checks")
    parser.add_argument("--gate", "-g", help="Run specific gate (A, B, C, or all)")
    parser.add_argument("--report", "-r", action="store_true", help="Generate report")
    parser.add_argument("--test", "-t", action="store_true", help="Run pytest")
    args = parser.parse_args()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "gates": {}
    }
    
    if args.gate:
        if args.gate == "all":
            for gate in ["A", "B", "C"]:
                results["gates"][gate] = run_gate_check(gate)
        else:
            results["gates"][args.gate] = run_gate_check(args.gate)
    else:
        # Run all gates by default
        for gate in ["A", "B", "C"]:
            results["gates"][gate] = run_gate_check(gate)
    
    if args.test:
        test_path = WORKSPACE / "tests" / "session_continuity" / "test_session_continuity_v11.py"
        results["pytest"] = run_pytest(test_path)
    
    # Output
    print(json.dumps(results, indent=2))
    
    if args.report:
        report = generate_report(results)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / "VALIDATION_REPORT.md"
        report_path.write_text(report)
        print(f"\nReport saved to: {report_path}")
    
    # Exit code
    all_passed = all(r.get("success", False) for r in results["gates"].values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()