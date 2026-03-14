# Plan Injection Patch - Unit Tests

## Overview

This document describes unit tests for the Plan Injection Patch.

## Test Categories

### 1. Gate Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `gate_allows_chat` | Normal chat message | Gate result: ALLOW |
| `gate_blocks_command` | Message starting with `/` | Gate result: SKIP |
| `gate_blocks_task_control` | `/approve`, `/deny`, etc. | Gate result: SKIP |
| `gate_blocks_tool_path` | Context has tool_result | Gate result: SKIP |
| `gate_respects_config_disabled` | `inject_plan_into_reply=false` | Gate result: DISABLED |
| `gate_respects_chat_only_config` | `plan_injection_for_chat_only=false` | Commands allowed |

### 2. Adapter Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `adapter_maps_tone` | Plan has tone=warm | Context receives tone=warm |
| `adapter_maps_key_points` | Plan has key_points array | Context receives key_points |
| `adapter_maps_constraints` | Plan has constraints | Context receives constraints |
| `adapter_maps_emotion` | Plan has emotion object | Context receives emotion |
| `adapter_maps_relationship` | Plan has relationship object | Context receives relationship |
| `adapter_handles_null` | Plan has null fields | Context receives null |

### 3. Schema Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `schema_validates_required_fields` | Missing tone | Schema invalid |
| `schema_validates_key_points_array` | key_points not array | Schema invalid |
| `schema_validates_emotion_object` | emotion not object | Schema invalid |
| `schema_accepts_valid_plan` | All valid fields | Schema valid |
| `schema_accepts_optional_fields` | Missing optional fields | Schema valid |

### 4. Fallback Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `fallback_disabled` | Feature disabled | No API call, normal response |
| `fallback_timeout` | API timeout > 5000ms | Skip plan, log warning |
| `fallback_connection_refused` | ECONNREFUSED | Skip plan, log error |
| `fallback_5xx` | HTTP 500-599 | Skip plan, log error |
| `fallback_4xx` | HTTP 400-499 | Skip plan, log warning |
| `fallback_schema_invalid` | Response doesn't match schema | Skip plan, log warning |
| `fallback_empty_plan` | Empty key_points | Use decision fallback |
| `fallback_soft_fail_false` | `soft_fail=false` | Throw error |

### 5. Config Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `config_default_enabled` | No config set | All features enabled |
| `config_master_switch` | `inject_plan_into_reply=false` | All injection disabled |
| `config_skip_commands` | `skip_plan_for_commands=false` | Commands allowed |
| `config_skip_task_control` | `skip_plan_for_task_control=false` | Task control allowed |
| `config_skip_tool_paths` | `skip_plan_for_tool_paths=false` | Tool paths allowed |
| `config_timeout` | `plan_injection_timeout_ms=1000` | Timeout at 1000ms |

## Test Implementation

### Test File Structure

```
OpenEmotion/
├── tests/
│   ├── plan_injection/
│   │   ├── test_gate.py
│   │   ├── test_adapter.py
│   │   ├── test_schema.py
│   │   ├── test_fallback.py
│   │   └── test_config.py
│   └── conftest.py
```

### Sample Test Code (Python)

```python
import pytest
from plan_injection import evaluate_gate, fetch_plan, validate_schema

class TestGate:
    def test_gate_allows_chat(self):
        message = {"body": "Hello, how are you?"}
        context = {}
        result = evaluate_gate(message, context)
        assert result["result"] == "allowed"

    def test_gate_blocks_command(self):
        message = {"body": "/status"}
        context = {}
        result = evaluate_gate(message, context)
        assert result["result"] == "skipped"
        assert result["reason"] == "is_command"

    def test_gate_blocks_task_control(self):
        message = {"body": "/approve"}
        context = {}
        result = evaluate_gate(message, context)
        assert result["result"] == "skipped"
        assert result["reason"] == "is_task_control"

    def test_gate_blocks_tool_path(self):
        message = {"body": "Check the logs"}
        context = {"tool_result": {"output": "logs..."}}
        result = evaluate_gate(message, context)
        assert result["result"] == "skipped"
        assert result["reason"] == "is_tool_path"

class TestSchema:
    def test_schema_validates_required_fields(self):
        plan = {"key_points": []}  # Missing tone
        assert validate_schema(plan) is False

    def test_schema_accepts_valid_plan(self):
        plan = {
            "tone": "warm",
            "intent": "repair",
            "key_points": ["acknowledge"],
            "constraints": [],
            "focus_target": "user",
            "emotion": {"valence": 0.5},
            "relationship": {"bond": 0.7}
        }
        assert validate_schema(plan) is True

class TestFallback:
    @pytest.mark.asyncio
    async def test_fallback_timeout(self, mock_timeout_api):
        result = await fetch_plan("user1", "Hello")
        assert result["success"] is False
        assert result["error"] == "timeout"
```

## Coverage Requirements

| Component | Minimum Coverage |
|-----------|-----------------|
| Gate logic | 100% |
| Adapter | 100% |
| Schema validation | 100% |
| Fallback handlers | 100% |
| Config parsing | 100% |
| **Overall** | **100%** |

## Running Tests

```bash
cd OpenEmotion
pytest tests/plan_injection/ -v --cov=plan_injection --cov-report=html
```

## Version

- **Version**: 1.0.0
- **Created**: 2026-03-13
