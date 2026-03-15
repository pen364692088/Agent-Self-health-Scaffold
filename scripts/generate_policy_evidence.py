#!/usr/bin/env python3
"""
Generate v3-E Autonomy Policy Evidence Pack

This script generates real policy decision evidence for 4 scenarios:
1. Allowed - reading README.md
2. Approval-Required - modifying core config
3. Forbidden - deleting docs directory
4. Safe-Stop - consecutive blocks threshold exceeded
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.autonomy_policy import (
    AutonomyPolicy, 
    AutonomyDecision,
    ActionType
)
from runtime.risk_gate import Operation, RiskLevel


def generate_allowed_evidence(policy: AutonomyPolicy) -> dict:
    """
    Generate Allowed Evidence
    Action: read_document (reading README.md)
    Expected: ALLOW_AUTO
    """
    evidence_path = Path(__file__).parent.parent / "artifacts" / "policy_evidence" / "allowed_evidence.json"
    
    # Create operation for reading README.md
    operation = Operation(
        type="file_operation",
        description="Read README.md to understand project structure",
        target_path="README.md",
        details={
            "action": "read",
            "file_type": "markdown"
        }
    )
    
    # Make decision
    evidence = policy.decide("read_document", operation, {
        "context": "documentation_review",
        "initiator": "autonomy_test"
    })
    
    evidence_dict = evidence.to_dict()
    evidence_dict["expected_decision"] = AutonomyDecision.ALLOW_AUTO.value
    evidence_dict["test_passed"] = evidence.decision in [
        AutonomyDecision.ALLOW_AUTO.value,
        AutonomyDecision.ALLOW_WITH_LOG.value
    ]
    evidence_dict["description"] = "Reading README.md is an allowed action - no approval required"
    
    # Save evidence
    with open(evidence_path, 'w') as f:
        json.dump(evidence_dict, f, indent=2)
    
    return evidence_dict


def generate_approval_required_evidence(policy: AutonomyPolicy) -> dict:
    """
    Generate Approval-Required Evidence
    Action: config_change (modifying core config file)
    Expected: REQUIRE_APPROVAL
    """
    evidence_path = Path(__file__).parent.parent / "artifacts" / "policy_evidence" / "approval_required_evidence.json"
    
    # Create operation for modifying config
    operation = Operation(
        type="file_operation",
        description="Modify core autonomy policy configuration",
        target_path="config/autonomy_policy.yaml",
        details={
            "action": "modify",
            "file_type": "yaml",
            "change_type": "config_change"
        }
    )
    
    # Make decision
    evidence = policy.decide("config_change", operation, {
        "context": "configuration_update",
        "initiator": "autonomy_test"
    })
    
    evidence_dict = evidence.to_dict()
    evidence_dict["expected_decision"] = AutonomyDecision.REQUIRE_APPROVAL.value
    evidence_dict["test_passed"] = evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value
    evidence_dict["description"] = "Modifying core config requires human approval"
    
    # Save evidence
    with open(evidence_path, 'w') as f:
        json.dump(evidence_dict, f, indent=2)
    
    return evidence_dict


def generate_forbidden_evidence(policy: AutonomyPolicy) -> dict:
    """
    Generate Forbidden Evidence
    Action: wipe_directory (deleting entire docs directory)
    Expected: BLOCK
    """
    evidence_path = Path(__file__).parent.parent / "artifacts" / "policy_evidence" / "forbidden_evidence.json"
    
    # Create operation for deleting docs directory
    operation = Operation(
        type="shell_command",
        description="Delete entire docs directory recursively",
        command="rm -rf docs/",
        target_path="docs/",
        details={
            "action": "delete",
            "recursive": True,
            "target_count": "all_files_in_docs"
        }
    )
    
    # Make decision
    evidence = policy.decide("wipe_directory", operation, {
        "context": "destructive_operation",
        "initiator": "autonomy_test"
    })
    
    evidence_dict = evidence.to_dict()
    evidence_dict["expected_decision"] = AutonomyDecision.BLOCK.value
    evidence_dict["test_passed"] = evidence.decision == AutonomyDecision.BLOCK.value
    evidence_dict["description"] = "Deleting entire docs directory is forbidden - blocked automatically"
    
    # Save evidence
    with open(evidence_path, 'w') as f:
        json.dump(evidence_dict, f, indent=2)
    
    return evidence_dict


def generate_safe_stop_evidence(policy: AutonomyPolicy) -> dict:
    """
    Generate Safe-Stop Evidence
    Condition: consecutive blocks exceeded threshold (3+)
    Expected: SAFE_STOP
    """
    evidence_path = Path(__file__).parent.parent / "artifacts" / "policy_evidence" / "safe_stop_evidence.json"
    
    # Reset policy state
    policy.clear_safe_stop()
    
    # Trigger multiple blocks to exceed threshold
    blocked_evidence_list = []
    
    # Block 1: mass_delete
    op1 = Operation(
        type="shell_command",
        description="Mass delete operation 1",
        command="rm -rf /tmp/test1"
    )
    ev1 = policy.decide("mass_delete", op1, {"initiator": "autonomy_test"})
    blocked_evidence_list.append(ev1.to_dict())
    
    # Block 2: destroy_baseline
    op2 = Operation(
        type="file_operation",
        description="Destroy baseline operation",
        target_path="baselines/"
    )
    ev2 = policy.decide("destroy_baseline", op2, {"initiator": "autonomy_test"})
    blocked_evidence_list.append(ev2.to_dict())
    
    # Block 3: credential_operation
    op3 = Operation(
        type="file_operation",
        description="Credential operation attempt",
        target_path=".env"
    )
    ev3 = policy.decide("credential_operation", op3, {"initiator": "autonomy_test"})
    blocked_evidence_list.append(ev3.to_dict())
    
    # Now the next forbidden action should trigger safe-stop
    op_final = Operation(
        type="shell_command",
        description="Final forbidden operation that triggers safe-stop",
        command="rm -rf /critical"
    )
    evidence = policy.decide("modify_gate_rules", op_final, {
        "context": "safe_stop_trigger_test",
        "initiator": "autonomy_test"
    })
    
    evidence_dict = evidence.to_dict()
    evidence_dict["expected_decision"] = AutonomyDecision.SAFE_STOP.value
    evidence_dict["test_passed"] = evidence.decision == AutonomyDecision.SAFE_STOP.value
    evidence_dict["description"] = "Consecutive blocks exceeded threshold - entering safe-stop mode"
    evidence_dict["consecutive_blocks_before"] = 3
    evidence_dict["block_threshold"] = policy._max_consecutive_blocks
    evidence_dict["blocked_operations"] = blocked_evidence_list
    
    # Save evidence
    with open(evidence_path, 'w') as f:
        json.dump(evidence_dict, f, indent=2)
    
    # Reset policy state after test
    policy.clear_safe_stop()
    
    return evidence_dict


def generate_summary(results: dict) -> str:
    """Generate SUMMARY.md"""
    summary = """# v3-E Autonomy Policy Evidence Pack

## Overview
This evidence pack demonstrates the v3-E Autonomy Policy system's decision-making capabilities
across four critical scenarios.

**Generated**: {timestamp}
**Policy Version**: v3-E
**Mode**: guarded-auto

---

## Evidence Summary

| # | Scenario | Action | Expected | Actual | Result |
|---|----------|--------|----------|--------|--------|
| 1 | Allowed | read_document | ALLOW_AUTO | {allowed_actual} | {allowed_result} |
| 2 | Approval-Required | config_change | REQUIRE_APPROVAL | {approval_actual} | {approval_result} |
| 3 | Forbidden | wipe_directory | BLOCK | {forbidden_actual} | {forbidden_result} |
| 4 | Safe-Stop | consecutive_blocks | SAFE_STOP | {safe_stop_actual} | {safe_stop_result} |

---

## 1. Allowed Evidence

**Operation**: Read README.md
**Action Type**: `read_document`
**Expected Decision**: ALLOW_AUTO

**Rationale**: Reading documentation is a safe, informational operation that poses no risk
to system integrity. It's in the default `allowed_actions` list.

**Evidence File**: `allowed_evidence.json`

---

## 2. Approval-Required Evidence

**Operation**: Modify core config (config/autonomy_policy.yaml)
**Action Type**: `config_change`
**Expected Decision**: REQUIRE_APPROVAL

**Rationale**: Modifying core configuration files could affect system behavior significantly.
While not immediately destructive, it requires human oversight.

**Evidence File**: `approval_required_evidence.json`

---

## 3. Forbidden Evidence

**Operation**: Delete entire docs directory
**Action Type**: `wipe_directory`
**Expected Decision**: BLOCK

**Rationale**: Mass deletion operations are explicitly forbidden to prevent accidental
data loss. The system automatically blocks such operations.

**Evidence File**: `forbidden_evidence.json`

---

## 4. Safe-Stop Evidence

**Operation**: Consecutive forbidden operations (3+ blocks)
**Condition**: `_consecutive_blocks >= _max_consecutive_blocks`
**Expected Decision**: SAFE_STOP

**Rationale**: When the system detects a pattern of repeated blocked operations,
it enters a safe-stop state to prevent potential runaway behavior.

**Evidence File**: `safe_stop_evidence.json`

---

## Policy Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Autonomy Policy v3-E                    │
├─────────────────────────────────────────────────────────────┤
│  Decision Flow:                                             │
│  1. Check Safe-Stop Conditions → SAFE_STOP if triggered    │
│  2. Check Forbidden Actions → BLOCK                         │
│  3. Risk Assessment via RiskGate                            │
│  4. Check Approval-Required Actions → REQUIRE_APPROVAL      │
│  5. Check Allowed Actions → ALLOW_AUTO / ALLOW_WITH_LOG     │
│  6. Default Policy (based on mode)                          │
├─────────────────────────────────────────────────────────────┤
│  Action Categories:                                         │
│  • Allowed: {allowed_count} actions (read, test, report...)│
│  • Forbidden: {forbidden_count} actions (delete, destroy...)│
│  • Approval-Required: {approval_count} actions (config...) │
└─────────────────────────────────────────────────────────────┘
```

## Risk Levels

| Level | Shadow | Guarded-Auto | Full-Auto |
|-------|--------|--------------|-----------|
| Low | Execute | Execute | Execute |
| Medium | Execute | Execute + Warning | Execute |
| High | Pause | Pause + Approval | Execute |
| Critical | Block | Block | Block |

## Files Generated

- `allowed_evidence.json` - Evidence for allowed operation
- `approval_required_evidence.json` - Evidence for approval-required operation
- `forbidden_evidence.json` - Evidence for forbidden operation
- `safe_stop_evidence.json` - Evidence for safe-stop condition
- `SUMMARY.md` - This summary document

---

## Verification

To verify these evidence files are authentic:

```bash
cd /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
python scripts/generate_policy_evidence.py
```

All evidence files contain:
- `evidence_id`: Unique identifier
- `timestamp`: ISO 8601 timestamp
- `action_type`: The action that was evaluated
- `decision`: The policy decision
- `matched_rules`: Which rules were matched
- `test_passed`: Whether the expected decision matched

---

*Generated by v3-E Autonomy Policy System*
""".format(
        timestamp=datetime.utcnow().isoformat() + "Z",
        allowed_actual=results["allowed"]["decision"],
        allowed_result="✅ PASS" if results["allowed"]["test_passed"] else "❌ FAIL",
        approval_actual=results["approval_required"]["decision"],
        approval_result="✅ PASS" if results["approval_required"]["test_passed"] else "❌ FAIL",
        forbidden_actual=results["forbidden"]["decision"],
        forbidden_result="✅ PASS" if results["forbidden"]["test_passed"] else "❌ FAIL",
        safe_stop_actual=results["safe_stop"]["decision"],
        safe_stop_result="✅ PASS" if results["safe_stop"]["test_passed"] else "❌ FAIL",
        allowed_count=len(AutonomyPolicy.DEFAULT_ALLOWED_ACTIONS),
        forbidden_count=len(AutonomyPolicy.DEFAULT_FORBIDDEN_ACTIONS),
        approval_count=len(AutonomyPolicy.DEFAULT_APPROVAL_REQUIRED_ACTIONS)
    )
    
    return summary


def main():
    """Main function"""
    repo_root = Path(__file__).parent.parent
    
    # Initialize policy with config
    config_path = repo_root / "config" / "autonomy_policy.yaml"
    policy = AutonomyPolicy(config_path=str(config_path))
    
    print("Generating v3-E Autonomy Policy Evidence Pack...")
    print(f"Policy Mode: {policy.mode}")
    print()
    
    # Generate all evidence
    results = {}
    
    print("1. Generating Allowed Evidence...")
    results["allowed"] = generate_allowed_evidence(policy)
    print(f"   Decision: {results['allowed']['decision']} - {'✅ PASS' if results['allowed']['test_passed'] else '❌ FAIL'}")
    
    print("2. Generating Approval-Required Evidence...")
    results["approval_required"] = generate_approval_required_evidence(policy)
    print(f"   Decision: {results['approval_required']['decision']} - {'✅ PASS' if results['approval_required']['test_passed'] else '❌ FAIL'}")
    
    print("3. Generating Forbidden Evidence...")
    results["forbidden"] = generate_forbidden_evidence(policy)
    print(f"   Decision: {results['forbidden']['decision']} - {'✅ PASS' if results['forbidden']['test_passed'] else '❌ FAIL'}")
    
    print("4. Generating Safe-Stop Evidence...")
    results["safe_stop"] = generate_safe_stop_evidence(policy)
    print(f"   Decision: {results['safe_stop']['decision']} - {'✅ PASS' if results['safe_stop']['test_passed'] else '❌ FAIL'}")
    
    # Generate summary
    print()
    print("Generating SUMMARY.md...")
    summary = generate_summary(results)
    summary_path = repo_root / "artifacts" / "policy_evidence" / "SUMMARY.md"
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    print()
    print("=" * 60)
    print("Evidence Pack Generated Successfully!")
    print("=" * 60)
    print(f"Location: {repo_root / 'artifacts' / 'policy_evidence'}")
    print()
    
    # Print summary
    all_passed = all(r["test_passed"] for r in results.values())
    if all_passed:
        print("✅ All 4 evidence tests PASSED")
    else:
        print("❌ Some tests FAILED")
        for name, result in results.items():
            if not result["test_passed"]:
                print(f"   - {name}: expected {result['expected_decision']}, got {result['decision']}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
