# Execution Policy Runbook

## Quick Reference

| Action | Tool |
|--------|------|
| Check policy before tool use | `policy-eval --path <path> --tool <tool>` |
| System health check | `policy-doctor` |
| View violations | `policy-violations-report` |
| Safe write | `safe-write <path> <content>` |
| Safe replace | `safe-replace <path> <old> <new>` |

---

## Common Scenarios

### Scenario 1: Edit ~/.openclaw/workspace/SOUL.md

**Incorrect (blocked by policy):**

    edit(path="~/.openclaw/workspace/SOUL.md", old="...", new="...")

**Policy Response:**

    DENY: OPENCLAW_PATH_NO_EDIT
    Reason: ~/.openclaw/** paths cannot use edit tool
    Fallback: Use safe-write, safe-replace, or exec + heredoc

**Correct:**

    # Using safe-replace
    safe-replace ~/.openclaw/workspace/SOUL.md "old text" "new text"

    # Or using exec + heredoc
    cat > ~/.openclaw/workspace/SOUL.md << 'EOF'
    new content
    EOF

### Scenario 2: Write to ~/.openclaw/config.json

**Incorrect:**

    write(path="~/.openclaw/config.json", content="...")

**Policy Response:**

    WARN: SENSITIVE_PATH_PREFER_SAFE_WRITE
    Reason: Direct write to sensitive paths should use verified tools
    Fallback: Prefer safe-write for atomic writes with verification

**Correct:**

    safe-write ~/.openclaw/config.json '{"key": "value"}'

### Scenario 3: Task Completion Message

**Incorrect:**

    message --action send --to user --message "任务已完成"

**Policy Response:**

    DENY: TASK_COMPLETION_PROTOCOL
    Reason: All completion messages must go through verification chain
    Fallback: Must use safe-message for completion messages

**Correct:**

    # First verify
    verify-and-close --task-id <id>

    # Then use safe-message
    safe-message --task-id <id> --message "任务已完成"

---

## Enforcement Levels

### P0: Hard Deny
- OPENCLAW_PATH_NO_EDIT
- GATE_REQUIRED_BEFORE_CLOSE
- HUMAN_FAILED_FORCES_REPAIR

### P1: Warn -> Deny on Repeat
- SENSITIVE_PATH_PREFER_SAFE_WRITE
- FRAGILE_REPLACE_BLOCK_ON_MANAGED_FILES
- PERSIST_BEFORE_REPLY
- TASK_COMPLETION_PROTOCOL

### P2: Warn Only
- EXTERNAL_PATH_WRITE_CAUTION
- LARGE_FILE_WRITE_CAUTION

---

## Troubleshooting

### Issue: Policy check returns DENY but I need to write

**Solution:**
1. Check if path matches sensitive pattern: `policy-eval --path <path>`
2. Use safe-write or safe-replace instead
3. If truly necessary, document reason and use exec + heredoc

### Issue: Violation count increasing

**Solution:**
1. Run `policy-violations-report --summary`
2. Identify recurring violations
3. Update code to use allowed tools
4. Consider rule promotion if violations persist

### Issue: False positive block

**Solution:**
1. Document the case in `artifacts/execution_policy/baseline/FALSE_POSITIVES.md`
2. Add exception to rules if warranted
3. Update test cases

---

## Rule Promotion Process

### When to Promote

A rule should be promoted from documentation -> warning -> enforcement when:
- Repeat violations >= 2 times
- Core path affected
- Delivery failure caused
- User explicit request

### Promotion Steps

1. **Identify pattern**: Review violation logs
2. **Draft rule**: Create YAML definition
3. **Test in warning mode**: Set action to "warn"
4. **Monitor**: Check for false positives
5. **Promote to deny**: Set action to "deny"

---

## Audit and Reporting

### Daily Violation Summary

    policy-violations-report --today --summary

### Violation Details

    policy-violations-report --rule-id OPENCLAW_PATH_NO_EDIT --detail

### Export for Analysis

    policy-violations-report --export csv --output violations.csv

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-09 | Initial runbook |
