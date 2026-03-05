#!/usr/bin/env python3
"""
E2E Tests for callback-handler v2.0

Gate B: Happy path + bad args
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
CALLBACK_HANDLER = WORKSPACE / "tools" / "callback-handler"
WORKFLOW_FILE = WORKSPACE / "WORKFLOW_STATE.json"

def run_callback_handler(*args):
    """Run callback-handler with args, return (stdout, stderr, exit_code)"""
    cmd = [str(CALLBACK_HANDLER)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def test_create_workflow_happy():
    """Happy path: create workflow"""
    # Clear first
    run_callback_handler("--clear")
    
    stdout, stderr, code = run_callback_handler(
        "--create",
        json.dumps({
            "steps": [
                {"id": "phase1", "task": "Task 1", "model": "test"},
                {"id": "phase2", "task": "Task 2", "model": "test"}
            ],
            "notify_on_done": "Done!"
        })
    )
    
    assert code == 0, f"Exit code {code}, stderr: {stderr}"
    result = json.loads(stdout)
    assert result["active"] == True
    assert len(result["steps"]) == 2
    assert result["steps"][0]["id"] == "phase1"
    print("✅ test_create_workflow_happy")
    return True

def test_activate_step_happy():
    """Happy path: activate step"""
    # Create workflow first (independent test)
    run_callback_handler("--clear")
    run_callback_handler("--create", json.dumps({
        "steps": [{"id": "phase1", "task": "Task 1", "model": "test"}]
    }))
    
    stdout, stderr, code = run_callback_handler("--activate", "phase1", "run_123")
    assert code == 0
    result = json.loads(stdout)
    assert result["success"] == True
    
    # Verify state
    stdout2, _, _ = run_callback_handler("--status")
    state = json.loads(stdout2)
    assert state["steps"][0]["run_id"] == "run_123"
    assert state["steps"][0]["status"] == "running"
    print("✅ test_activate_step_happy")
    return True

def test_callback_spawn_next():
    """Happy path: callback returns spawn_next"""
    # Create 2-step workflow
    run_callback_handler("--clear")
    run_callback_handler("--create", json.dumps({
        "steps": [
            {"id": "phase1", "task": "Task 1", "model": "test"},
            {"id": "phase2", "task": "Task 2", "model": "test"}
        ],
        "notify_on_done": "Done!"
    }))
    run_callback_handler("--activate", "phase1", "run_123")
    
    stdout, stderr, code = run_callback_handler("run_123")
    assert code == 0
    result = json.loads(stdout)
    assert result["action"] == "spawn_next"
    assert result["should_silence"] == True
    assert result["next_step"]["id"] == "phase2"
    print("✅ test_callback_spawn_next")
    return True

def test_callback_notify_user():
    """Happy path: final callback returns notify_user"""
    # Create 1-step workflow
    run_callback_handler("--clear")
    run_callback_handler("--create", json.dumps({
        "steps": [{"id": "phase1", "task": "Task 1", "model": "test"}],
        "notify_on_done": "Done!"
    }))
    
    # Activate and complete phase1
    run_callback_handler("--activate", "phase1", "run_456")
    stdout, _, _ = run_callback_handler("run_456")
    result = json.loads(stdout)
    assert result["action"] == "notify_user"
    assert result["message"] == "Done!"
    assert result["should_silence"] == False
    print("✅ test_callback_notify_user")
    return True

def test_callback_no_workflow():
    """Bad args: callback with no workflow file"""
    run_callback_handler("--clear")
    stdout, stderr, code = run_callback_handler("run_xxx")
    result = json.loads(stdout)
    assert result["action"] == "ignore"
    assert result["reason"] == "no_workflow_file"
    print("✅ test_callback_no_workflow")
    return True

def test_status_empty():
    """Happy path: status with no workflow"""
    run_callback_handler("--clear")
    stdout, stderr, code = run_callback_handler("--status")
    assert code == 0
    assert "No active workflow" in stdout
    print("✅ test_status_empty")
    return True

def test_clear():
    """Happy path: clear workflow"""
    # Create first
    run_callback_handler("--create", json.dumps({"steps": [{"id": "x", "task": "y", "model": "z"}]}))
    assert WORKFLOW_FILE.exists()
    
    # Clear
    stdout, _, _ = run_callback_handler("--clear")
    assert not WORKFLOW_FILE.exists()
    print("✅ test_clear")
    return True

def test_schema_validation():
    """Gate A: output conforms to schema"""
    import jsonschema
    
    schema_path = WORKSPACE / "schemas" / "callback-handler.v1.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Create workflow
    run_callback_handler("--clear")
    run_callback_handler("--create", json.dumps({
        "steps": [{"id": "a", "task": "b", "model": "c"}],
        "notify_on_done": "Done"
    }))
    run_callback_handler("--activate", "a", "run_schema")
    
    # Validate output
    stdout, _, _ = run_callback_handler("run_schema")
    result = json.loads(stdout)
    
    # Should validate
    jsonschema.validate(result, schema)
    print("✅ test_schema_validation")
    return True

def main():
    tests = [
        test_create_workflow_happy,
        test_activate_step_happy,
        test_callback_spawn_next,
        test_callback_notify_user,
        test_callback_no_workflow,
        test_status_empty,
        test_clear,
        test_schema_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            # Cleanup before each test
            run_callback_handler("--clear")
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
        finally:
            # Cleanup after each test
            run_callback_handler("--clear")
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)
    
    print("✅ All tests passed")
    sys.exit(0)

if __name__ == "__main__":
    main()
