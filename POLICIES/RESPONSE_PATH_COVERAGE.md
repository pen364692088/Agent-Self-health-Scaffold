# Response Path Coverage Policy v1.0

**Purpose**: Ensure all user-visible output paths are covered by SRAP governance chain.
**Effective Date**: 2026-03-06
**Applies To**: All new and existing response generation paths.

---

## Overview

Every path that produces user-visible output MUST declare its governance coverage:

```
User Request → Response Path → [interpreter? → contract? → checker? → shadow log?] → Output
```

Uncovered paths are a **security risk** and will be blocked by the Coverage Gate.

---

## Governance Chain Components

| Component | Purpose | Required |
|-----------|---------|----------|
| `interpreter` | Parses self-report claims | ✅ Yes |
| `contract` | Intent alignment contract | ✅ Yes |
| `checker` | Consistency checker | ✅ Yes |
| `shadow_log` | Logs to shadow_log.jsonl | ✅ Yes (Shadow Mode) |

---

## Path Categories

### Category A: Full Coverage
- **Definition**: Path passes through all 4 components
- **Status**: ✅ APPROVED
- **Examples**: Main chat response, emotiond bridge output

### Category B: Partial Coverage
- **Definition**: Path passes through interpreter + checker, but bypasses contract
- **Status**: ⚠️ REQUIRES REVIEW
- **Examples**: Debug endpoints, admin tools

### Category C: No Coverage
- **Definition**: Path does not pass through any governance component
- **Status**: ❌ BLOCKED
- **Examples**: Direct file writes, raw LLM output

---

## Path Inventory Format

```json
{
  "path_id": "main_chat_response",
  "description": "Primary chat response generation",
  "components": {
    "interpreter": true,
    "contract": true,
    "checker": true,
    "shadow_log": true
  },
  "category": "A",
  "owner": "emotiond-enforcer",
  "last_audit": "2026-03-06"
}
```

---

## Gate Requirements

### New Path Registration
1. Declare path in `artifacts/self_report/response_path_inventory.json`
2. Specify which components are used
3. If Category B/C, provide justification
4. Run `check-response-path-coverage` tool
5. Gate FAIL → cannot deploy

### Existing Path Audit
1. All existing paths must be registered
2. Category C paths must be migrated or removed
3. Category B paths must have documented justification
4. Audit frequency: weekly

---

## Coverage Checker Tool

```bash
# Check all registered paths
~/.openclaw/workspace/tools/check-response-path-coverage

# Check specific path
~/.openclaw/workspace/tools/check-response-path-coverage --path main_chat_response

# Audit mode (strict)
~/.openclaw/workspace/tools/check-response-path-coverage --audit
```

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | All paths covered |
| 1 | Partial coverage (Category B exists) |
| 2 | Uncovered paths (Category C exists) |
| 3 | Invalid/missing inventory file |

---

## Gate Integration

This policy integrates with Tool Delivery Gates:

| Gate | Check |
|------|-------|
| Gate A | Path inventory schema valid |
| Gate B | New paths tested with coverage checker |
| Gate C | Coverage checker health check |

---

## Remediation

### Category C → Category A
1. Route output through interpreter
2. Apply intent contract
3. Run consistency checker
4. Enable shadow logging
5. Re-run coverage checker

### Category B → Category A
1. Add missing components
2. Document reason for bypass (if intentional)
3. Re-run coverage checker

---

## Inventory File

See `artifacts/self_report/response_path_inventory.json` for current path registry.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-06 | Initial creation from MVP11.6 Task 5 |

