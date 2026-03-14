# Plan Injection Patch - E2E Tests

## Overview

This document describes end-to-end tests for the Plan Injection Patch.

## Test Scenarios

### 1. Normal Chat Flow

| Test | User Action | Expected System Behavior | Verification |
|------|-------------|-------------------------|--------------|
| `e2e_normal_chat_injection` | Send "Hello" | Plan injected, warm reply | context.json has plan, reply is warm |
| `e2e_emotional_chat_injection` | Send "I'm feeling down" | Plan reflects empathy tone | tone=soft, key_points include empathy |
| `e2e_boundary_chat_injection` | Send repeated demands | Plan reflects boundary tone | tone=guarded, constraints set |

### 2. New Task Request

| Test | User Action | Expected System Behavior | Verification |
|------|-------------|-------------------------|--------------|
| `e2e_new_task_no_interruption` | Request new coding task | Task starts, plan doesn't interrupt | Task created, tools called normally |
| `e2e_task_with_chat` | Chat during task | Plan injected for chat parts | Chat replies use plan, task unaffected |

### 3. Continue/Control/Waiting Paths

| Test | User Action | Expected System Behavior | Verification |
|------|-------------|-------------------------|--------------|
| `e2e_continue_no_misinjection` | Task in progress, send "continue" | No plan injection | injection_metadata shows skipped |
| `e2e_control_no_misinjection` | Send `/approve` | No plan injection | Command works, no plan |
| `e2e_waiting_no_misinjection` | Task waiting for input | No plan injection | Waiting state unchanged |

### 4. OpenEmotion Down Scenario

| Test | Setup | User Action | Expected System Behavior |
|------|-------|-------------|-------------------------|
| `e2e_emotiond_down_normal_reply` | Stop emotiond | Send chat message | Normal reply, fallback triggered |
| `e2e_emotiond_down_no_block` | Stop emotiond | Start task | Task runs normally |
| `e2e_emotiond_restart` | Restart emotiond | Send chat | Plan injection resumes |

### 5. Tool Execution Unaffected

| Test | User Action | Expected System Behavior | Verification |
|------|-------------|-------------------------|--------------|
| `e2e_tools_selected_correctly` | Task requiring read/write tools | Correct tools called | Tool calls match task needs |
| `e2e_tool_results_unchanged` | Run tools with plan enabled | Results same as without plan | Compare tool outputs |
| `e2e_no_tool_side_effects` | Multi-tool task | No unexpected tool calls | Only expected tools called |

### 6. Checkpoint Unaffected

| Test | User Action | Expected System Behavior | Verification |
|------|-------------|-------------------------|--------------|
| `e2e_checkpoint_hash_unchanged` | Create checkpoint with plan enabled | Checkpoint same as without plan | Compare checkpoint hashes |
| `e2e_checkpoint_recovery` | Recover from checkpoint | Recovery works normally | State restored correctly |

### 7. Task State Unaffected

| Test | User Action | Expected System Behavior | Verification |
|------|-------------|-------------------------|--------------|
| `e2e_task_state_transitions` | Run task to completion | State transitions same as without plan | State log matches expected |
| `e2e_task_resume` | Pause and resume task | Resume works correctly | Task continues from pause point |

### 8. Control Commands Unaffected

| Test | Command | Expected Behavior | Verification |
|------|---------|-------------------|--------------|
| `e2e_approve_works` | `/approve` | Approves pending action | Action approved |
| `e2e_deny_works` | `/deny` | Denies pending action | Action denied |
| `e2e_cancel_works` | `/cancel` | Cancels current task | Task cancelled |
| `e2e_status_works` | `/status` | Shows status | Status displayed |

## Test Implementation

### Test File Structure

```
OpenEmotion/
├── tests/
│   ├── e2e/
│   │   ├── test_plan_injection_chat_flow.py
│   │   ├── test_plan_injection_task_flow.py
│   │   ├── test_plan_injection_control_flow.py
│   │   ├── test_plan_injection_fallback_flow.py
│   │   └── test_plan_injection_isolation.py
│   └── conftest.py
```

### Sample Test Code (Python)

```python
import pytest
import time
import json
import subprocess

class TestE2ENormalChat:
    def test_e2e_normal_chat_injection(self, telegram_client, emotiond_running):
        """Normal chat should have plan injected"""
        # Send message via Telegram
        telegram_client.send_message("Hello, how are you?")
        
        # Wait for reply
        reply = telegram_client.wait_for_reply(timeout=30)
        
        # Verify plan was injected
        with open("/home/user/.openclaw/workspace/emotiond/context.json") as f:
            context = json.load(f)
        
        assert context.get("plan") is not None
        assert context["injection_metadata"]["gate_result"] == "allowed"
        
        # Verify reply exists and has reasonable content
        assert len(reply) > 0

class TestE2ETaskFlow:
    def test_e2e_new_task_no_interruption(self, telegram_client, emotiond_running):
        """New task should not be interrupted by plan injection"""
        # Request a coding task
        telegram_client.send_message("Create a hello world Python script")
        
        # Wait for task to start
        time.sleep(5)
        
        # Check that task was created
        status = telegram_client.send_command("/status")
        
        # Task should be running or completed
        assert "running" in status or "completed" in status
        
        # Tools should have been called
        context = self.get_context()
        # Task execution should proceed normally
        # (plan injection should not have interfered)

class TestE2EControlFlow:
    def test_e2e_control_no_misinjection(self, telegram_client, emotiond_running):
        """Control commands should not have plan injection"""
        # Start a task
        telegram_client.send_message("List files in /tmp")
        time.sleep(2)
        
        # Send control command
        reply = telegram_client.send_command("/status")
        
        # Check context - plan should be skipped
        with open("/home/user/.openclaw/workspace/emotiond/context.json") as f:
            context = json.load(f)
        
        assert context["injection_metadata"]["gate_result"] == "skipped"
        assert context["injection_metadata"]["reason"] == "is_task_control"

class TestE2EFallback:
    def test_e2e_emotiond_down_normal_reply(self, telegram_client):
        """System should work when emotiond is down"""
        # Stop emotiond
        subprocess.run(["pkill", "-f", "emotiond"])
        time.sleep(2)
        
        # Send message
        telegram_client.send_message("Hello!")
        reply = telegram_client.wait_for_reply(timeout=30)
        
        # Should get normal reply
        assert len(reply) > 0
        
        # Context should show fallback
        with open("/home/user/.openclaw/workspace/emotiond/context.json") as f:
            context = json.load(f)
        
        assert context["injection_metadata"]["fallback_triggered"] is True
        
        # Restart emotiond
        subprocess.Popen(["python", "-m", "emotiond.api"])
```

## Test Environment

### Required Components

| Component | Version | Purpose |
|-----------|---------|---------|
| OpenClaw Gateway | 2026.3.x | Main runtime |
| emotiond | v0.1.0 | OpenEmotion API |
| Telegram Bot | - | Chat interface |
| Test User | - | telegram:8420019401 |

### Environment Setup

```bash
# 1. Start emotiond
cd ~/.openclaw/workspace/OpenEmotion
source .venv/bin/activate
python -m emotiond.api &

# 2. Start OpenClaw Gateway
openclaw gateway start

# 3. Verify services
curl http://127.0.0.1:18080/health
openclaw status

# 4. Run E2E tests
pytest tests/e2e/plan_injection/ -v
```

## Test Data

### Sample Conversations

```json
[
  {
    "id": "normal_chat_1",
    "messages": ["Hello!", "How are you?", "What can you do?"],
    "expected_injection": true
  },
  {
    "id": "command_1",
    "messages": ["/status", "/help", "/new"],
    "expected_injection": false
  },
  {
    "id": "task_1",
    "messages": ["Create a Python script that prints hello"],
    "expected_tool_calls": ["write", "exec"],
    "expected_injection_for_chat_parts": true
  }
]
```

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| All E2E tests pass | 100% |
| No regressions in existing features | Manual verification |
| Plan injection only affects reply text | Integration test verification |
| Fallback works in all scenarios | All fallback tests pass |
| Performance impact < 100ms | Latency measurement |

## Running Tests

```bash
# Full E2E suite
pytest tests/e2e/plan_injection/ -v --timeout=300

# Specific test
pytest tests/e2e/plan_injection/test_plan_injection_chat_flow.py -v

# With reporting
pytest tests/e2e/plan_injection/ -v --html=report.html
```

## Version

- **Version**: 1.0.0
- **Created**: 2026-03-13
