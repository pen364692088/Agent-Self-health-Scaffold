# Plan Injection Patch - Integration Tests

## Overview

This document describes integration tests for the Plan Injection Patch.

## Test Scenarios

### 1. Chat Path Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `chat_requests_plan` | 1. Send chat message<br>2. Check context.json | Plan fields present |
| `chat_plan_affects_reply` | 1. Send chat message<br>2. Get plan with tone=warm<br>3. Generate reply | Reply has warm tone |
| `chat_plan_key_points_used` | 1. Send chat message<br>2. Get plan with key_points<br>3. Generate reply | Reply addresses key points |

### 2. Command Path Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `command_no_plan_request` | 1. Send `/status`<br>2. Check context.json | No plan in context |
| `command_normal_execution` | 1. Send `/status`<br>2. Verify command runs | Command executes normally |
| `command_reply_no_plan` | 1. Send `/help`<br>2. Check reply | Reply generated without plan |

### 3. Task Control Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `task_control_no_plan` | 1. Start task<br>2. Send `/approve`<br>3. Check context | No plan in context |
| `task_control_unaffected` | 1. Start task<br>2. Enable plan injection<br>3. Run task | Task execution unchanged |

### 4. Tool Path Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `tool_path_no_plan` | 1. Call tool<br>2. Check context during tool execution | No plan in context |
| `tool_execution_unaffected` | 1. Enable plan injection<br>2. Execute tools | Tool results unchanged |
| `tool_selection_unaffected` | 1. Enable plan injection<br>2. Run task with tools | Same tools selected |

### 5. Fallback Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `plan_failure_normal_reply` | 1. Disable emotiond<br>2. Send chat message<br>3. Check reply | Normal reply generated |
| `plan_timeout_normal_reply` | 1. Set timeout to 1ms<br>2. Send message<br>3. Check reply | Normal reply generated |
| `plan_5xx_normal_reply` | 1. Mock 500 error<br>2. Send message<br>3. Check reply | Normal reply generated |
| `plan_schema_invalid_reply` | 1. Mock invalid schema<br>2. Send message<br>3. Check reply | Normal reply generated |

### 6. Event Flow Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `event_still_written_after_plan` | 1. Send message<br>2. Get plan<br>3. Generate reply<br>4. Check /event | world_event still sent |
| `decision_still_fetched_after_plan` | 1. Send message<br>2. Get plan<br>3. Check context | decision present |
| `plan_and_decision_coexist` | 1. Send message<br>2. Check context.json | Both plan and decision present |

## Test Implementation

### Test File Structure

```
OpenEmotion/
├── tests/
│   ├── integration/
│   │   ├── test_plan_injection_chat.py
│   │   ├── test_plan_injection_command.py
│   │   ├── test_plan_injection_task.py
│   │   ├── test_plan_injection_tool.py
│   │   ├── test_plan_injection_fallback.py
│   │   └── test_plan_injection_events.py
│   └── conftest.py
```

### Sample Test Code (Python)

```python
import pytest
import requests
import json

EMOTIOND_URL = "http://127.0.0.1:18080"
CONTEXT_FILE = "/home/user/.openclaw/workspace/emotiond/context.json"

class TestChatIntegration:
    def test_chat_requests_plan(self, chat_session):
        # Send chat message
        response = chat_session.send_message("How are you feeling?")
        
        # Check context has plan
        with open(CONTEXT_FILE) as f:
            context = json.load(f)
        
        assert "plan" in context
        assert context["plan"]["tone"] in ["soft", "warm", "guarded", "cold"]
        assert len(context["plan"]["key_points"]) > 0

    def test_chat_plan_affects_reply(self, chat_session, mock_warm_plan):
        mock_warm_plan()  # Set emotiond to return warm tone
        
        response = chat_session.send_message("Hello!")
        
        # Reply should have warm tone characteristics
        assert any(word in response.lower() for word in ["glad", "appreciate", "warm"])

class TestCommandIntegration:
    def test_command_no_plan_request(self, chat_session):
        response = chat_session.send_message("/status")
        
        with open(CONTEXT_FILE) as f:
            context = json.load(f)
        
        # Plan should be null for commands
        assert context.get("plan") is None
        assert context["injection_metadata"]["gate_result"] == "skipped"

class TestFallbackIntegration:
    def test_plan_failure_normal_reply(self, chat_session, emotiond_down):
        emotiond_down()  # Stop emotiond
        
        response = chat_session.send_message("Hello!")
        
        # Should still get a normal reply
        assert len(response) > 0
        assert "error" not in response.lower()

class TestEventFlowIntegration:
    def test_event_still_written_after_plan(self, chat_session, emotiond_logs):
        chat_session.send_message("Thanks for your help!")
        
        # Check that world_event was still sent
        logs = emotiond_logs.get_events()
        world_events = [e for e in logs if e["type"] == "world_event"]
        
        assert len(world_events) > 0
```

## Test Environment

### Required Services

| Service | Port | Purpose |
|---------|------|---------|
| emotiond | 18080 | OpenEmotion API |
| OpenClaw Gateway | 3000 | Message handling |
| Context file | - | ~/.openclaw/workspace/emotiond/context.json |

### Test Data

| Data | Description |
|------|-------------|
| `test_user_id` | telegram:1234567890 |
| `test_messages.json` | Sample messages for testing |
| `expected_plans.json` | Expected plan responses |

## Running Tests

```bash
# Start emotiond
cd OpenEmotion && python -m emotiond.api &

# Run integration tests
pytest tests/integration/plan_injection/ -v

# With coverage
pytest tests/integration/plan_injection/ -v --cov=plan_injection
```

## Success Criteria

- All integration tests pass
- No regressions in existing functionality
- Plan injection only affects reply text
- Fallback works in all scenarios
- Event flow continues normally

## Version

- **Version**: 1.0.0
- **Created**: 2026-03-13
