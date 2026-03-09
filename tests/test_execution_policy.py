#!/usr/bin/env python3
"""
Test suite for OPENCLAW_EXECUTION_POLICY.md compliance.

Three rounds:
1. Happy path - verify normal completion works
2. Failure path - verify missing steps are blocked
3. Human failed path - verify repair cycle works
4. Extended - binding validation + interceptor
"""

import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any

# Setup paths - use environment variable or relative path for CI compatibility
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).parent.parent))
TOOLS = WORKSPACE / "tools"
ARTIFACTS = WORKSPACE / "artifacts" / "receipts"
WORKFLOW_STATE = WORKSPACE / "WORKFLOW_STATE.json"

VERIFY_AND_CLOSE = TOOLS / "verify-and-close"
DONE_GUARD = TOOLS / "done-guard"


def run_tool(tool_path: str, args: list) -> tuple:
    """Run a tool and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [tool_path] + args,
        capture_output=True,
        text=True,
        cwd=WORKSPACE
    )
    return result.returncode, result.stdout, result.stderr


def cleanup_receipts(task_id: str):
    """Remove all receipts for a task."""
    for rtype in ["contract", "e2e", "preflight", "final"]:
        path = ARTIFACTS / f"{task_id}_{rtype}_receipt.json"
        if path.exists():
            path.unlink()


def check_receipt_exists(task_id: str, rtype: str) -> bool:
    """Check if a receipt exists."""
    path = ARTIFACTS / f"{task_id}_{rtype}_receipt.json"
    return path.exists()


def load_receipt(task_id: str, rtype: str) -> Dict:
    """Load receipt content."""
    path = ARTIFACTS / f"{task_id}_{rtype}_receipt.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# =============================================================================
# Round 1: Happy Path Tests
# =============================================================================

def test_verify_and_close_happy_path():
    """Test 1.1: Normal completion should work."""
    task_id = "test_happy_path_001"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(VERIFY_AND_CLOSE), ["--task-id", task_id, "--json"])
        assert code == 0, f"verify-and-close failed: {err}"
        
        result = json.loads(out)
        assert result["result"] == "READY_TO_CLOSE", f"Unexpected result: {result['result']}"
        
        for rtype in ["contract", "e2e", "preflight", "final"]:
            assert check_receipt_exists(task_id, rtype), f"Missing {rtype} receipt"
        
        code, out, err = run_tool(str(DONE_GUARD), ["--task-id", task_id, "--all", "--json"])
        guard_result = json.loads(out)
        assert guard_result["can_close"] == True, f"done-guard blocked: {guard_result['blockers']}"
        
        print(f"✅ test_verify_and_close_happy_path PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_verify_and_close_happy_path FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_receipt_field_stability():
    """Test 1.2: Receipt fields should be stable and complete."""
    task_id = "test_receipt_fields_001"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(VERIFY_AND_CLOSE), ["--task-id", task_id, "--json"])
        assert code == 0, f"verify-and-close failed: {err}"
        
        required_fields = ["task_id", "receipt_type", "status", "generated_at"]
        for rtype in ["contract", "e2e", "preflight", "final"]:
            receipt = load_receipt(task_id, rtype)
            for field in required_fields:
                assert field in receipt, f"Missing field '{field}' in {rtype} receipt"
        
        final = load_receipt(task_id, "final")
        assert "gate_results" in final, "Missing gate_results in final receipt"
        assert "artifacts" in final, "Missing artifacts in final receipt"
        
        print(f"✅ test_receipt_field_stability PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_receipt_field_stability FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


# =============================================================================
# Round 2: Failure Path Tests
# =============================================================================

def test_done_guard_blocks_fake_done_without_receipts():
    """Test 2.1: Missing receipts should block completion."""
    task_id = "test_missing_receipts_001"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(DONE_GUARD), ["--task-id", task_id, "--all", "--json"])
        result = json.loads(out)
        
        assert result["can_close"] == False, "Should be blocked without receipts"
        assert len(result["blockers"]) > 0, "Should have blockers"
        
        print(f"✅ test_done_guard_blocks_fake_done_without_receipts PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_done_guard_blocks_fake_done_without_receipts FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_missing_single_receipt_blocked():
    """Test 2.2: Missing any single receipt should block."""
    task_id = "test_partial_receipts_001"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(VERIFY_AND_CLOSE), ["--task-id", task_id, "--json"])
        assert code == 0
        
        final_path = ARTIFACTS / f"{task_id}_final_receipt.json"
        final_path.unlink()
        
        code, out, err = run_tool(str(DONE_GUARD), ["--task-id", task_id, "--all", "--json"])
        result = json.loads(out)
        assert result["can_close"] == False, "Should be blocked with missing final receipt"
        
        print(f"✅ test_missing_single_receipt_blocked PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_missing_single_receipt_blocked FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_fake_completion_text_blocked():
    """Test 2.3: Text with fake completion phrases should be blocked."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("任务已完成，所有功能测试通过，可以交付")
        temp_file = f.name
    
    try:
        code, out, err = run_tool(str(DONE_GUARD), ["--check-text", temp_file, "--json"])
        result = json.loads(out)
        
        assert result["has_fake_completion"] == True, "Should detect fake completion"
        assert result["action"] == "BLOCK", "Should block"
        
        print(f"✅ test_fake_completion_text_blocked PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_fake_completion_text_blocked FAILED: {e}")
        return False
    finally:
        os.unlink(temp_file)


def test_invalid_state_transition_blocked():
    """Test 2.4: Invalid state transitions should be blocked."""
    code, out, err = run_tool(str(DONE_GUARD), ["--validate-state", "implementing:ready_to_close", "--json"])
    
    try:
        result = json.loads(out)
        assert result["valid"] == False, "Should be invalid transition"
        
        print(f"✅ test_invalid_state_transition_blocked PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_invalid_state_transition_blocked FAILED: {e}")
        return False


# =============================================================================
# Round 3: Human Failed Path Tests
# =============================================================================

def test_human_failed_forces_repairing():
    """Test 3.1: Human failed feedback should force repairing state."""
    task_id = "test_human_failed_001"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(VERIFY_AND_CLOSE), ["--task-id", task_id, "--json"])
        assert code == 0, "Should complete successfully"
        
        code, out, err = run_tool(str(DONE_GUARD), ["--validate-state", "human_failed:ready_to_close", "--json"])
        result = json.loads(out)
        assert result["valid"] == False, "human_failed -> ready_to_close should be blocked"
        
        code, out, err = run_tool(str(DONE_GUARD), ["--validate-state", "human_failed:repairing", "--json"])
        result = json.loads(out)
        assert result["valid"] == True, "human_failed -> repairing should be valid"
        
        print(f"✅ test_human_failed_forces_repairing PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_human_failed_forces_repairing FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_repairing_cannot_skip_to_close():
    """Test 3.2: Repairing state cannot skip reverify."""
    code, out, err = run_tool(str(DONE_GUARD), ["--validate-state", "repairing:ready_to_close", "--json"])
    
    try:
        result = json.loads(out)
        assert result["valid"] == False, "repairing -> ready_to_close should be blocked"
        
        print(f"✅ test_repairing_cannot_skip_to_close PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_repairing_cannot_skip_to_close FAILED: {e}")
        return False


def test_reverify_required_after_repair():
    """Test 3.3: After repair, must go through reverify."""
    try:
        code, out, err = run_tool(str(DONE_GUARD), ["--validate-state", "repairing:reverify", "--json"])
        result = json.loads(out)
        assert result["valid"] == True, "repairing -> reverify should be valid"
        
        code, out, err = run_tool(str(DONE_GUARD), ["--validate-state", "reverify:ready_to_close", "--json"])
        result = json.loads(out)
        assert result["valid"] == True, "reverify -> ready_to_close should be valid"
        
        print(f"✅ test_reverify_required_after_repair PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_reverify_required_after_repair FAILED: {e}")
        return False


# =============================================================================
# Extended Tests: Binding Validation + Interceptor
# =============================================================================

def test_receipt_validator_binding():
    """Test E.1: Receipt validator should verify task_id consistency."""
    task_id = "test_validator_001"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(VERIFY_AND_CLOSE), ["--task-id", task_id, "--json"])
        assert code == 0
        
        validator = TOOLS / "receipt-validator"
        code, out, err = run_tool(str(validator), ["--task-id", task_id, "--json"])
        
        result = json.loads(out)
        assert result["valid"] == True, f"Should be valid: {result.get('issues', [])}"
        
        print(f"✅ test_receipt_validator_binding PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_receipt_validator_binding FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_output_interceptor_blocks():
    """Test E.2: Output interceptor should block protected channels."""
    task_id = "test_interceptor_001"
    cleanup_receipts(task_id)
    
    try:
        interceptor = TOOLS / "output-interceptor"
        code, out, err = run_tool(str(interceptor), [
            "--task-id", task_id,
            "--channel", "telegram",
            "--message", "任务已完成",
            "--json"
        ])
        
        result = json.loads(out)
        assert result["action"] == "BLOCK", f"Should block: {result}"
        
        print(f"✅ test_output_interceptor_blocks PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_output_interceptor_blocks FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_output_interceptor_allows():
    """Test E.3: Output interceptor should allow with receipts."""
    task_id = "test_interceptor_002"
    cleanup_receipts(task_id)
    
    try:
        code, out, err = run_tool(str(VERIFY_AND_CLOSE), ["--task-id", task_id, "--json"])
        assert code == 0
        
        interceptor = TOOLS / "output-interceptor"
        code, out, err = run_tool(str(interceptor), [
            "--task-id", task_id,
            "--channel", "telegram",
            "--message", "实现完成",
            "--json"
        ])
        
        result = json.loads(out)
        assert result["action"] == "ALLOW", f"Should allow: {result}"
        
        print(f"✅ test_output_interceptor_allows PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_output_interceptor_allows FAILED: {e}")
        return False
    finally:
        cleanup_receipts(task_id)


def test_metrics_collection():
    """Test E.4: Metrics should be collectable."""
    try:
        metrics_tool = TOOLS / "execution-metrics"
        code, out, err = run_tool(str(metrics_tool), ["--collect", "--json"])
        
        result = json.loads(out)
        assert "metrics" in result
        
        print(f"✅ test_metrics_collection PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_metrics_collection FAILED: {e}")
        return False


# =============================================================================
# Main
# =============================================================================

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("OPENCLAW EXECUTION POLICY TEST SUITE v1.1")
    print("=" * 60)
    print()
    
    tests = [
        # Round 1: Happy Path
        ("1.1", test_verify_and_close_happy_path),
        ("1.2", test_receipt_field_stability),
        
        # Round 2: Failure Path
        ("2.1", test_done_guard_blocks_fake_done_without_receipts),
        ("2.2", test_missing_single_receipt_blocked),
        ("2.3", test_fake_completion_text_blocked),
        ("2.4", test_invalid_state_transition_blocked),
        
        # Round 3: Human Failed Path
        ("3.1", test_human_failed_forces_repairing),
        ("3.2", test_repairing_cannot_skip_to_close),
        ("3.3", test_reverify_required_after_repair),
        
        # Extended Tests
        ("E.1", test_receipt_validator_binding),
        ("E.2", test_output_interceptor_blocks),
        ("E.3", test_output_interceptor_allows),
        ("E.4", test_metrics_collection),
    ]
    
    results = []
    for test_id, test_fn in tests:
        print(f"\n[{test_id}] {test_fn.__name__}")
        passed = test_fn()
        results.append((test_id, passed))
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for test_id, p in results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"  [{test_id}] {status}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
