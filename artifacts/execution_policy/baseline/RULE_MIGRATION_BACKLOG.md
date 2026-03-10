# Rule Migration Backlog

This document tracks rules that should be migrated from documentation to enforcement.

## Classification

| Class | Description | Action |
|-------|-------------|--------|
| A | Must be engineered (hard enforcement) | Implement in execution-policy-enforcer |
| B | Warning level (soft enforcement) | Log violations, warn users |
| C | Documentation only | Keep in SOUL.md/TOOLS.md |

---

## A-Class Rules (Must Engineer)

### 1. OPENCLAW_PATH_NO_EDIT ✅ DONE
**Status**: Implemented
**Priority**: P0
**Scope**: `~/.openclaw/**`
**Trigger**: edit tool
**Action**: DENY
**Fallback**: safe-write, safe-replace, exec + heredoc

### 2. GATE_REQUIRED_BEFORE_CLOSE ✅ DONE
**Status**: Implemented
**Priority**: P0
**Scope**: task_close action
**Action**: DENY
**Fallback**: verify-and-close

### 3. TASK_COMPLETION_PROTOCOL ✅ DONE
**Status**: Implemented
**Priority**: P1
**Scope**: completion messages
**Action**: DENY
**Fallback**: safe-message

---

## B-Class Rules (Warning)

### 1. SENSITIVE_PATH_PREFER_SAFE_WRITE ✅ DONE
**Status**: Implemented
**Priority**: P1
**Scope**: `~/.openclaw/**`
**Trigger**: write tool
**Action**: WARN
**Fallback**: safe-write

### 2. PERSIST_BEFORE_REPLY
**Status**: Pending
**Priority**: P1
**Scope**: reply with state change
**Action**: WARN
**Fallback**: Persist to SESSION-STATE.md first

### 3. FRAGILE_REPLACE_BLOCK_ON_MANAGED_FILES ✅ DONE
**Status**: Implemented
**Priority**: P1
**Scope**: `~/.openclaw/**/*.md`
**Trigger**: edit tool with replace
**Action**: DENY
**Fallback**: safe-replace

---

## C-Class Rules (Documentation)

### 1. EXTERNAL_PATH_WRITE_CAUTION
**Status**: Documentation only
**Location**: SOUL.md
**Description**: External paths may have different access controls

### 2. LARGE_FILE_WRITE_CAUTION
**Status**: Documentation only
**Location**: SOUL.md
**Description**: Large writes may cause timeout or context issues

---

## Promotion Criteria

Rules should be promoted from C → B → A when:

1. **Repeat violations ≥ 2 times**: If the same rule is violated multiple times
2. **Core path affected**: If ~/.openclaw/** is involved
3. **Delivery failure caused**: If the violation caused a failed delivery
4. **User explicit request**: If user specifically requested enforcement

---

## Migration Log

| Date | Rule | From | To | Reason |
|------|------|------|-----|--------|
| 2026-03-09 | OPENCLAW_PATH_NO_EDIT | Documentation | A-Class | Frequent violations |
| 2026-03-09 | GATE_REQUIRED_BEFORE_CLOSE | Documentation | A-Class | Delivery integrity |
| 2026-03-09 | SENSITIVE_PATH_PREFER_SAFE_WRITE | Documentation | B-Class | Path safety |
| 2026-03-09 | TASK_COMPLETION_PROTOCOL | Documentation | A-Class | Completion bypass |
| 2026-03-09 | FRAGILE_REPLACE_BLOCK_ON_MANAGED_FILES | Documentation | A-Class | Edit failures |

---

## Pending Migrations

| Rule | Target Class | Blocker | Priority |
|------|--------------|---------|----------|
| PERSIST_BEFORE_REPLY | B-Class | Need runtime hook | Medium |
| HUMAN_FAILED_FORCES_REPAIR | A-Class | Need state integration | High |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-09 | Initial backlog creation |
