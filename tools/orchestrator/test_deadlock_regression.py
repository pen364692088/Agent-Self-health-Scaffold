#!/usr/bin/env python3
"""
Deadlock Regression Test for Orchestrator

Tests that spawn_task does NOT deadlock when calling _save_pending_to_storage.
This was a bug where Lock() + nested with self.lock: caused deadlock.
Fix: Split into _locked() versions, or use RLock().

Run: python3 test_deadlock_regression.py
"""

import sys
import time
import threading
import tempfile
import shutil
import json
import re
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator, SubtaskStatus

# Constants for timeouts (not used for timing assertions, just to prevent hanging)
DEADLOCK_TIMEOUT = 2.0  # If spawn takes longer than this, it's deadlocked
CONCURRENT_TIMEOUT = 5.0  # For concurrent tests


def test_spawn_task_no_deadlock():
    """Test that spawn_task completes without deadlock"""
    print("Test 1: spawn_task no deadlock...")
    
    orch = Orchestrator()
    
    # Use thread + timeout to detect deadlock
    result = [None]
    exc = [None]
    
    def do_spawn():
        try:
            task_id, run_id, session_key = orch.spawn_task(
                description="Test task",
                model="test-model"
            )
            result[0] = (task_id, run_id, session_key)
        except Exception as e:
            exc[0] = e
    
    t = threading.Thread(target=do_spawn)
    t.start()
    t.join(timeout=DEADLOCK_TIMEOUT)
    
    # Assertion: thread should have completed (not deadlocked)
    assert not t.is_alive(), f"spawn_task deadlocked (thread still running after {DEADLOCK_TIMEOUT}s)"
    assert exc[0] is None, f"spawn_task raised exception: {exc[0]}"
    assert result[0] is not None, "spawn_task returned None"
    
    task_id, run_id, session_key = result[0]
    assert task_id.startswith("task_"), f"Invalid task_id: {task_id}"
    assert run_id.startswith("run_"), f"Invalid run_id: {run_id}"
    assert session_key, "session_key should not be empty"
    
    print(f"  ✅ spawn_task completed without deadlock")
    return True


def test_concurrent_spawn():
    """Test that multiple concurrent spawn_task calls work correctly"""
    print("Test 2: concurrent spawn_task...")
    
    # Clean storage first
    import os
    temp_dir = tempfile.mkdtemp()
    try:
        orch = Orchestrator(workspace_dir=temp_dir)
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def spawn_one(i):
            try:
                task_id, run_id, session_key = orch.spawn_task(
                    description=f"Concurrent task {i}",
                    model="test-model"
                )
                with lock:
                    results.append((task_id, run_id))
            except Exception as e:
                with lock:
                    errors.append(e)
        
        threads = [threading.Thread(target=spawn_one, args=(i,)) for i in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=CONCURRENT_TIMEOUT)
        
        # Assertion: all threads completed
        alive_threads = [t for t in threads if t.is_alive()]
        assert len(alive_threads) == 0, f"{len(alive_threads)} threads still running (deadlock or too slow)"
        
        # Assertion: no errors
        assert len(errors) == 0, f"Errors during concurrent spawn: {errors}"
        
        # Assertion: all 10 completed
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"
        
        # Assertion: no duplicate task_ids
        task_ids = [r[0] for r in results]
        assert len(set(task_ids)) == 10, "Duplicate task_ids detected!"
        
        # Assertion: storage file is valid JSON
        storage_file = Path(temp_dir) / "tools" / "orchestrator" / "pending_subtasks.json"
        assert storage_file.exists(), "Storage file should exist"
        with open(storage_file) as f:
            data = json.load(f)
        assert 'pending' in data, "Storage file missing 'pending' key"
        assert len(data['pending']) == 10, f"Storage should have 10 pending, got {len(data['pending'])}"
        
        print(f"  ✅ 10 concurrent spawns completed correctly")
        print(f"  ✅ No duplicate task_ids")
        print(f"  ✅ Storage file valid with 10 tasks")
        return True
    finally:
        shutil.rmtree(temp_dir)


def test_attach_subtask_no_deadlock():
    """Test that attach_subtask also works (it has similar lock pattern)"""
    print("Test 3: attach_subtask no deadlock...")
    
    orch = Orchestrator()
    
    result = [None]
    exc = [None]
    
    def do_attach():
        try:
            task_id = orch.attach_subtask(
                run_id="test_run",
                child_session_key="test_session",
                description="Test attach"
            )
            result[0] = task_id
        except Exception as e:
            exc[0] = e
    
    t = threading.Thread(target=do_attach)
    t.start()
    t.join(timeout=DEADLOCK_TIMEOUT)
    
    assert not t.is_alive(), f"attach_subtask deadlocked"
    assert exc[0] is None, f"attach_subtask raised exception: {exc[0]}"
    assert result[0] is not None, "attach_subtask returned None"
    
    print(f"  ✅ attach_subtask completed without deadlock")
    return True


def test_gc_no_deadlock():
    """Test that gc method works (it also calls _save_pending_to_storage)"""
    print("Test 4: gc no deadlock...")
    
    orch = Orchestrator()
    
    # Create some tasks
    for i in range(3):
        orch.spawn_task(description=f"Task {i}", model="test")
    
    result = [None]
    exc = [None]
    
    def do_gc():
        try:
            removed = orch.gc(keep_days=0)  # Remove all
            result[0] = removed
        except Exception as e:
            exc[0] = e
    
    t = threading.Thread(target=do_gc)
    t.start()
    t.join(timeout=DEADLOCK_TIMEOUT)
    
    assert not t.is_alive(), f"gc deadlocked"
    assert exc[0] is None, f"gc raised exception: {exc[0]}"
    
    print(f"  ✅ gc completed without deadlock, removed {result[0]} tasks")
    return True


def test_storage_persistence():
    """Test that tasks are correctly persisted and reloaded"""
    print("Test 5: storage persistence...")
    
    # Create a temp workspace
    temp_dir = tempfile.mkdtemp()
    try:
        orch1 = Orchestrator(workspace_dir=temp_dir)
        
        # Create tasks
        task_id1, _, _ = orch1.spawn_task(description="Task 1", model="test")
        task_id2, _, _ = orch1.spawn_task(description="Task 2", model="test")
        
        # Verify storage file exists and is valid JSON
        storage_file = Path(temp_dir) / "tools" / "orchestrator" / "pending_subtasks.json"
        assert storage_file.exists(), "Storage file should exist"
        
        with open(storage_file) as f:
            data = json.load(f)
        assert 'pending' in data
        assert len(data['pending']) == 2
        
        # Create new orchestrator to reload
        orch2 = Orchestrator(workspace_dir=temp_dir)
        
        assert len(orch2.pending_subtasks) == 2, f"Expected 2 pending tasks, got {len(orch2.pending_subtasks)}"
        assert task_id1 in orch2.pending_subtasks
        assert task_id2 in orch2.pending_subtasks
        
        print(f"  ✅ Tasks persisted and reloaded correctly")
        return True
    finally:
        shutil.rmtree(temp_dir)


def test_race_condition_amplified():
    """Test with amplified race conditions (monkeypatch sleep in _locked)"""
    print("Test 6: race condition amplified...")
    
    # Create temp workspace
    temp_dir = tempfile.mkdtemp()
    try:
        orch = Orchestrator(workspace_dir=temp_dir)
        
        # Monkeypatch to add delay in _locked (amplify race window)
        original_locked = orch._save_pending_to_storage_locked
        
        def slow_locked():
            time.sleep(0.05)  # 50ms delay
            return original_locked()
        
        orch._save_pending_to_storage_locked = slow_locked
        
        # Now run concurrent spawns
        results = []
        errors = []
        lock = threading.Lock()
        
        def spawn_one(i):
            try:
                task_id, run_id, _ = orch.spawn_task(
                    description=f"Race test {i}",
                    model="test"
                )
                with lock:
                    results.append((task_id, run_id))
            except Exception as e:
                with lock:
                    errors.append(e)
        
        threads = [threading.Thread(target=spawn_one, args=(i,)) for i in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=CONCURRENT_TIMEOUT)
        
        # Check all completed
        alive = [t for t in threads if t.is_alive()]
        assert len(alive) == 0, f"{len(alive)} threads still running"
        assert len(errors) == 0, f"Errors: {errors}"
        
        # Check no duplicates
        task_ids = [r[0] for r in results]
        assert len(set(task_ids)) == len(task_ids), "Duplicate task_ids in race test!"
        
        # Check storage consistency
        storage_file = Path(temp_dir) / "tools" / "orchestrator" / "pending_subtasks.json"
        with open(storage_file) as f:
            data = json.load(f)
        
        assert len(data['pending']) == len(results), \
            f"Storage has {len(data['pending'])} tasks, but {len(results)} were created"
        
        print(f"  ✅ Race condition test passed with {len(results)} concurrent spawns")
        return True
    finally:
        shutil.rmtree(temp_dir)


def test_cli_command_registration():
    """Test that all CLI commands have valid handlers (prevent cmd_gc drift)"""
    print("Test 7: CLI command registration check...")
    
    # Read the CLI script and check for handler functions
    cli_path = Path(__file__).parent.parent / "subtask-orchestrate"
    
    with open(cli_path) as f:
        content = f.read()
    
    # Expected commands and their handlers
    expected_commands = {
        'run': 'cmd_run',
        'detect': 'cmd_detect',
        'join': 'cmd_join',
        'gc': 'cmd_gc',
        'stuck': 'cmd_stuck',
        'list': 'cmd_list',
    }
    
    missing = []
    for cmd_name, handler_name in expected_commands.items():
        # Check if function is defined
        pattern = rf'def {handler_name}\('
        if not re.search(pattern, content):
            missing.append(f"{cmd_name} -> {handler_name}")
    
    assert len(missing) == 0, f"Missing handlers: {missing}"
    
    print(f"  ✅ All {len(expected_commands)} CLI commands have valid handlers")
    return True


def main():
    print("=" * 50)
    print("Orchestrator Deadlock Regression Tests")
    print("=" * 50)
    print()
    
    tests = [
        test_spawn_task_no_deadlock,
        test_concurrent_spawn,
        test_attach_subtask_no_deadlock,
        test_gc_no_deadlock,
        test_storage_persistence,
        test_race_condition_amplified,
        test_cli_command_registration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            import traceback
            print(f"  ❌ FAILED: {e}")
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

