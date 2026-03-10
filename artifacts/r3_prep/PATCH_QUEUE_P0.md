# Patch Queue P0

**Generated**: 2026-03-10 06:50 CST
**Version**: 1.0
**Status**: PLANNING - No execution during freeze

---

## P0-1: Block Direct Message Tool Completion Path

### Summary
Prevent `message` tool from being used directly for completion messages, forcing use of `safe-message`.

### Affected Files

| File | Change Type |
|------|-------------|
| `tools/safe-message` | Enhancement |
| `tools/output-interceptor` | Enhancement |
| `hooks/execution-policy-enforcer/enforcer.py` | Enhancement (optional) |
| `POLICIES/EXECUTION_POLICY_RULES.yaml` | New rule |
| `SOUL.md` | Documentation |

### Current Behavior

```python
# Agent can call message tool directly
message --action send --to user --message "任务已完成"
# This bypasses all policy checks
```

### New Behavior

```python
# Option A: Runtime-level check (requires OpenClaw core change)
def message_tool_check(message, channel):
    if contains_completion_pattern(message):
        return BLOCK("Use safe-message for completion messages")

# Option B: Hook-level check (feasible now)
# execution-policy-enforcer checks message content before send
```

### Implementation

**Phase 1: Documentation + Warning**

```python
# safe-message: Add warning about direct message tool
def main():
    print("""
    WARNING: Do not use message tool directly for completion messages.
    Use safe-message to ensure policy compliance.
    """)
```

**Phase 2: Pattern Detection in output-interceptor**

```python
# output-interceptor: Add completion pattern check

COMPLETION_PATTERNS = [
    r"已完成", r"全部完成", r"可以交付", r"任务完成",
    r"task.*complete", r"finished", r"done", r"✅.*完成"
]

def check_completion_content(message: str) -> tuple:
    """Check if message contains completion patterns."""
    for pattern in COMPLETION_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return True, pattern
    return False, None

def intercept_message(task_id, channel, message):
    # Check for completion patterns
    is_completion, pattern = check_completion_content(message)
    
    if is_completion:
        # Require safe-message usage
        return {
            "action": "BLOCK",
            "reason": "completion_requires_safe_message",
            "pattern": pattern
        }
    return {"action": "ALLOW"}
```

**Phase 3: Policy Rule**

```yaml
# EXECUTION_POLICY_RULES.yaml

- id: COMPLETION_MESSAGE_REQUIRES_SAFE_MESSAGE
  priority: P0
  status: active
  trigger:
    tools: ["message"]
    content_patterns:
      - "已完成"
      - "全部完成"
      - "可以交付"
      - "任务完成"
  action: DENY
  message: "Use safe-message for completion messages"
  bypass: none
```

### Risk Level

| Aspect | Risk | Mitigation |
|--------|------|------------|
| Breaking valid messages | LOW | Pattern is specific |
| False positives | MEDIUM | Allow override with audit |
| User confusion | LOW | Clear error message |

### Rollback Method

```bash
# If issues arise
git checkout HEAD~1 -- tools/output-interceptor
git checkout HEAD~1 -- POLICIES/EXECUTION_POLICY_RULES.yaml

# Or disable the rule
sed -i 's/status: active/status: disabled/' POLICIES/EXECUTION_POLICY_RULES.yaml
```

### Required Tests

```python
# tests/test_completion_message_block.py

def test_completion_pattern_detected():
    """Verify completion patterns are detected."""
    result = output_interceptor("--task-id", "test", "--message", "任务已完成")
    assert result["action"] == "BLOCK"

def test_normal_message_allowed():
    """Verify normal messages pass through."""
    result = output_interceptor("--task-id", "test", "--message", "Hello world")
    assert result["action"] == "ALLOW"

def test_safe_message_allowed():
    """Verify safe-message with receipt passes."""
    # Create receipt first
    verify_and_close("--task-id", "test", "--skip-e2e")
    result = safe_message("--task-id", "test", "--message", "任务已完成")
    assert result["action"] == "ALLOW"
```

### Dependency Order

```
1. Update output-interceptor with pattern detection
2. Update EXECUTION_POLICY_RULES.yaml
3. Update SOUL.md documentation
4. Run tests
5. Monitor for false positives
```

### Evidence to Collect

```bash
# During observation window, check for:
grep -c "任务.*完成\|已完成\|可以交付" logs/messages.log
# How often do completion messages occur via direct message tool?
```

---

## P0-2: Add Receipt Check to finalize-response

### Summary
Require verify-and-close receipt before finalize-response allows completion output.

### Affected Files

| File | Change Type |
|------|-------------|
| `tools/finalize-response` | Enhancement |
| `tests/test_finalize_response.py` | New test |

### Current Behavior

```python
# finalize-response checks:
# 1. Fake completion patterns
# 2. Receipts existence (BUT doesn't enforce)

def check_receipts_exist(task_id):
    # Only checks, doesn't block
    return len(missing) == 0, missing
```

### New Behavior

```python
# finalize-response ENFORCES receipt requirement

def check_receipts_exist(task_id):
    required = ["final"]  # At minimum, final receipt
    missing = []
    
    for rtype in required:
        path = ARTIFACTS_DIR / f"{task_id}_{rtype}_receipt.json"
        if not path.exists():
            missing.append(rtype)
    
    if missing:
        return {
            "action": "BLOCK",
            "reason": "missing_receipts",
            "missing": missing,
            "hint": f"Run verify-and-close --task-id {task_id} first"
        }
    
    return {"action": "ALLOW"}
```

### Implementation

```python
# tools/finalize-response v1.2

def main():
    # ... existing code ...
    
    # ENFORCE receipt check (change from warning to block)
    receipts_ok, missing = check_receipts_exist(args.task_id)
    
    if not receipts_ok:
        result["action"] = "BLOCK"
        result["reason"] = "missing_receipts"
        result["missing"] = missing
        result["hint"] = f"Run verify-and-close --task-id {args.task_id} first"
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ BLOCK: Missing receipts: {missing}")
            print(f"   Run: verify-and-close --task-id {args.task_id}")
        
        return 1  # Exit with error code
    
    # Continue with fake completion check
    # ...
```

### Risk Level

| Aspect | Risk | Mitigation |
|--------|------|------------|
| Breaking existing workflow | MEDIUM | Provide clear guidance |
| Missing receipt edge cases | LOW | At least require final receipt |
| User confusion | LOW | Clear error message |

### Rollback Method

```bash
# If issues arise
git checkout HEAD~1 -- tools/finalize-response

# Or relax requirement
# Change: required = ["final"]
# To:     required = []  # No enforcement
```

### Required Tests

```python
# tests/test_finalize_response_receipt.py

def test_block_without_receipt():
    """Verify finalize-response blocks without receipt."""
    result = finalize_response("--task-id", "no_receipt_task", "--summary", "Done")
    assert result["action"] == "BLOCK"
    assert "missing_receipts" in result["reason"]

def test_allow_with_receipt():
    """Verify finalize-response allows with receipt."""
    # Create receipt
    create_receipt("test_task", "final")
    
    result = finalize_response("--task-id", "test_task", "--summary", "Done")
    assert result["action"] == "ALLOW"

def test_fake_completion_blocked_even_with_receipt():
    """Verify fake completion is still blocked."""
    create_receipt("test_task", "final")
    
    result = finalize_response("--task-id", "test_task", "--summary", "已完成")
    assert result["action"] == "BLOCK"
    assert "fake_completion" in result["reason"]
```

### Dependency Order

```
1. Update finalize-response to enforce receipt check
2. Update error messages
3. Run tests
4. Document in SOUL.md
```

---

## P0-3: Remove or Neutralize safe-message --force

### Summary
Remove the `--force` flag that bypasses policy checks, or convert it to audit-only mode.

### Affected Files

| File | Change Type |
|------|-------------|
| `tools/safe-message` | Breaking change |
| `SOUL.md` | Documentation |
| `tests/test_safe_message.py` | Update tests |

### Current Behavior

```python
# safe-message --force bypasses all checks

if args.force:
    print("[FORCED] Would send...")
    return 0  # Success without any check
```

### New Behavior

**Option A: Remove entirely**

```python
# Remove --force argument entirely
parser.add_argument("--force", action="store_true", 
                    help="DEPRECATED: Force mode removed")

if args.force:
    print("ERROR: --force mode has been removed.")
    print("Use message tool directly for emergency sends.")
    return 2
```

**Option B: Audit-only mode (recommended)**

```python
# --force still works but logs to audit

if args.force:
    # Log to audit
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "FORCE_SEND",
        "task_id": task_id,
        "channel": channel,
        "message_preview": message[:100],
        "session_key": os.environ.get("OPENCLAW_SESSION_KEY", "unknown")
    }
    
    audit_log = WORKSPACE / "artifacts" / "audit" / "force_send_audit.jsonl"
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_log, "a") as f:
        f.write(json.dumps(audit_entry) + "\n")
    
    # Still proceed, but with audit trail
    print(f"⚠️  FORCE SEND (audit logged): {channel}")
    # Continue with actual send...
```

### Implementation (Option B - Recommended)

```python
# tools/safe-message v1.1

def audit_force_send(task_id, channel, message):
    """Log force send to audit trail."""
    audit_dir = WORKSPACE / "artifacts" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "FORCE_SEND",
        "task_id": task_id,
        "channel": channel,
        "message_length": len(message),
        "message_preview": message[:100],
        "session_key": os.environ.get("OPENCLAW_SESSION_KEY", "unknown")
    }
    
    audit_file = audit_dir / "force_send_audit.jsonl"
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return entry

def main():
    # ... existing code ...
    
    if args.force:
        # Audit the force send
        audit_entry = audit_force_send(task_id, channel, message)
        
        # Warn user
        if not args.json:
            print(f"⚠️  FORCE SEND AUDITED")
            print(f"   Audit ID: {audit_entry['timestamp']}")
            print(f"   Channel: {channel}")
            print(f"   Message: {message[:50]}...")
        
        # Proceed with send (direct to message tool)
        # ... actual send logic ...
```

### Risk Level

| Aspect | Risk | Mitigation |
|--------|------|------------|
| Breaking emergency sends | LOW | Still works with audit |
| Audit log growth | LOW | Rotate logs |
| User confusion | LOW | Clear warning message |

### Rollback Method

```bash
# If issues arise
git checkout HEAD~1 -- tools/safe-message

# Or disable audit requirement
# Comment out audit_force_send() call
```

### Required Tests

```python
# tests/test_safe_message_force.py

def test_force_creates_audit_entry():
    """Verify --force creates audit log entry."""
    result = safe_message(
        "--task-id", "test",
        "--channel", "telegram",
        "--message", "Emergency message",
        "--force"
    )
    
    # Check audit log
    audit_log = WORKSPACE / "artifacts" / "audit" / "force_send_audit.jsonl"
    assert audit_log.exists()
    
    entries = [json.loads(line) for line in audit_log.read_text().strip().split("\n")]
    assert any(e["task_id"] == "test" for e in entries)

def test_normal_send_no_audit():
    """Verify normal send doesn't create audit entry."""
    # Create receipt first
    verify_and_close("--task-id", "test", "--skip-e2e")
    
    safe_message(
        "--task-id", "test",
        "--channel", "telegram",
        "--message", "Normal message"
    )
    
    # Check no force audit entry
    audit_log = WORKSPACE / "artifacts" / "audit" / "force_send_audit.jsonl"
    if audit_log.exists():
        entries = [json.loads(line) for line in audit_log.read_text().strip().split("\n")]
        assert not any(e["task_id"] == "test" and e["action"] == "FORCE_SEND" for e in entries)
```

### Dependency Order

```
1. Create audit directory structure
2. Update safe-message with audit logic
3. Update tests
4. Update documentation
5. Monitor audit log
```

---

## P0 Summary

| Patch | Risk | Rollback | Tests Required |
|-------|------|----------|----------------|
| P0-1 | LOW-MEDIUM | Easy | 3 tests |
| P0-2 | MEDIUM | Easy | 3 tests |
| P0-3 | LOW | Easy | 2 tests |

**Total Tests Required**: 8 new tests

**Estimated Implementation Time**: 2-3 hours

**Recommended Execution Order**: P0-2 → P0-3 → P0-1
