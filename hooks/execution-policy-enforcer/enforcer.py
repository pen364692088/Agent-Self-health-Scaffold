#!/usr/bin/env python3
"""
Execution Policy Enforcer Hook

This hook runs before tool execution to enforce execution policies.
It should be called by the OpenClaw runtime before each tool invocation.

Usage: execution-policy-enforcer --tool <tool> --path <path> [--operation <op>]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add tools directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "tools"))

# Import the policy evaluator
try:
    from policy_eval import evaluate, load_rules
except ImportError:
    # Fallback if import fails
    RULES_FILE = Path.home() / ".openclaw" / "workspace" / "POLICIES" / "EXECUTION_POLICY_RULES.yaml"
    VIOLATIONS_DIR = Path.home() / ".openclaw" / "workspace" / "artifacts" / "execution_policy" / "violations"
    
    import yaml
    import re
    from datetime import datetime
    
    def load_rules():
        if not RULES_FILE.exists():
            return {"metadata": {"version": "1.0.0"}, "rules": []}
        with open(RULES_FILE) as f:
            return yaml.safe_load(f)
    
    def expand_path(path: str) -> str:
        return os.path.expanduser(path)
    
    def match_path_pattern(path: str, pattern: str) -> bool:
        expanded_path = expand_path(path)
        expanded_pattern = expand_path(pattern)
        if "**" in expanded_pattern:
            regex_pattern = expanded_pattern.replace("**", ".*")
            regex_pattern = regex_pattern.replace("*", "[^/]*")
            return bool(re.match(f"^{regex_pattern}", expanded_path))
        return expanded_path.startswith(expanded_pattern.rstrip("*"))
    
    def log_violation(rule_id: str, decision: str, path: str, tool: str, session_key: str = ""):
        VIOLATIONS_DIR.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "rule_id": rule_id,
            "decision": decision,
            "path": path,
            "tool": tool,
            "session_key": session_key
        }
        log_file = VIOLATIONS_DIR / f"violations_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def evaluate(path: str, tool: str, operation: str = "write", session_key: str = "") -> dict:
        rules_data = load_rules()
        rules = rules_data.get("rules", [])
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        rules.sort(key=lambda r: priority_order.get(r.get("priority", "P2"), 2))
        
        for rule in rules:
            if rule.get("status") != "active":
                continue
            
            trigger = rule.get("trigger", {})
            
            # Check path pattern
            if "path_pattern" in trigger:
                if not match_path_pattern(path, trigger["path_pattern"]):
                    continue
            
            # Check tools
            if "tools" in trigger:
                if tool not in trigger["tools"]:
                    continue
            
            if "tool" in trigger:
                if tool != trigger["tool"]:
                    continue
            
            # Check operation
            if "operation" in trigger:
                if operation != trigger["operation"]:
                    continue
            
            # Rule matched
            action = rule["action"]
            if action in ["deny", "warn"]:
                log_violation(rule["id"], action, path, tool, session_key)
            
            return {
                "decision": action,
                "rule_id": rule["id"],
                "reason": rule.get("reason", ""),
                "fallback": rule.get("fallback", "")
            }
        
        return {"decision": "allow", "rule_id": None, "message": "No policy violations"}


def main():
    parser = argparse.ArgumentParser(description="Execution policy enforcer")
    parser.add_argument("--tool", required=True, help="Tool name to check")
    parser.add_argument("--path", help="Target path (if applicable)")
    parser.add_argument("--operation", default="write", help="Operation type")
    parser.add_argument("--session-key", default="", help="Session key for logging")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--strict", action="store_true", help="Exit with error on deny")
    
    args = parser.parse_args()
    
    # If no path, just allow (not all tools need path checking)
    if not args.path:
        if args.json:
            print(json.dumps({"decision": "allow", "reason": "No path to check"}))
        else:
            print("ALLOW: No path to check")
        sys.exit(0)
    
    result = evaluate(args.path, args.tool, args.operation, args.session_key)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Decision: {result['decision'].upper()}")
        if result.get("rule_id"):
            print(f"Rule: {result['rule_id']}")
        if result.get("reason"):
            print(f"Reason: {result['reason']}")
        if result.get("fallback"):
            print(f"Fallback: {result['fallback']}")
    
    # Exit with error code if denied and strict mode
    if result["decision"] == "deny" and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
