# Mutation Guard Policy

## Document Info
- **Version**: v1.0
- **Date**: 2026-03-16
- **Status**: ACTIVE
- **Enforcement**: MANDATORY

---

## 1. Purpose

Define mutation guard policy to ensure all write operations undergo canonical target resolution before execution, preventing truth source fragmentation.

---

## 2. Scope

### 2.1 Covered Operations
All operations that modify state/files:
- File creation
- File modification
- File deletion
- State updates
- Configuration changes
- Registry updates

### 2.2 Canonical Objects
Objects with single source of truth:

| Object Name | Type | Write Policy |
|-------------|------|--------------|
| unified_program_state | State | update_only |
| unified_progress_ledger | Ledger | update_only |
| canonical_index | Index | update_only |
| session_state | State | update_only |
| handoff_document | Document | create_update |

---

## 3. Canonical Object Definition

### 3.1 What Makes an Object Canonical
1. **Single source of truth** - One authoritative file per repository
2. **Cross-session persistence** - Must survive session boundaries
3. **Agent-independent** - Not tied to specific agent instance
4. **Mutation-sensitive** - Incorrect writes cause fragmentation

### 3.2 Canonical Object Properties

```yaml
canonical_object:
  name: string                    # Object identifier
  description: string             # Human-readable description
  allowed_targets:
    - repo: string                # Repository name
      path: string                # Canonical file path
      write_policy: enum          # update_only | create_update | append_only
  forbidden_actions:
    - string                      # List of forbidden actions
  ambiguity_policy: enum          # block | escalate | fallback
```

---

## 4. Write Policies

### 4.1 Policy Types

| Policy | Description | Allowed Actions | Forbidden Actions |
|--------|-------------|-----------------|-------------------|
| update_only | Only update existing | modify | create, delete |
| create_update | Create or update | create, modify | delete |
| append_only | Only append data | append | create, modify, delete |

### 4.2 Policy Enforcement

**BEFORE any write operation:**
1. Resolve object name → canonical path
2. Check write policy
3. Verify action allowed
4. Execute or block

---

## 5. Ambiguity Policy

### 5.1 When Ambiguity Occurs
- Multiple candidate paths match
- No path matches but object exists in registry
- Registry inconsistent or corrupted

### 5.2 Ambiguity Behavior

| Policy | Behavior |
|--------|----------|
| **block** | Do NOT proceed. Output error with details. |
| escalate | Prompt user for confirmation. |
| fallback | Use fallback path (requires explicit fallback defined). |

### 5.3 Default Policy
**DEFAULT: block**

For canonical objects, ambiguity MUST block, not guess.

---

## 6. Forbidden Actions

### 6.1 Universally Forbidden
- Creating duplicate canonical files
- Creating alternative truth sources
- Deleting canonical files without explicit approval
- Modifying canonical files without preflight

### 6.2 Object-Specific Forbidden
Defined per object in CANONICAL_OBJECT_REGISTRY.yaml

---

## 7. Mutation Gate Structure

### 7.1 Gate Sequence

```
Gate M1: Object Resolve
         ↓
Gate M2: Canonical Resolve
         ↓
Gate M3: Policy Check
         ↓
Gate M4: Evidence Echo
         ↓
Gate M5: Execute or Block
```

### 7.2 Gate Details

#### Gate M1 - Object Resolve
- **Input**: Task semantics
- **Output**: Canonical object name
- **Fail**: Cannot determine object → proceed (non-canonical operation)

#### Gate M2 - Canonical Resolve
- **Input**: Object name
- **Output**: Canonical target path
- **Fail**: Ambiguity or not found → block if canonical

#### Gate M3 - Policy Check
- **Input**: Target path, intended action
- **Output**: ALLOW or BLOCK
- **Fail**: Policy violation → block with reason

#### Gate M4 - Evidence Echo
- **Input**: All resolved information
- **Output**: Structured evidence log
- **Fail**: Logging failure → warn but proceed

#### Gate M5 - Execute or Block
- **Input**: Gate decision
- **Output**: Execute mutation or return blocked
- **Fail**: Block with clear error message

---

## 8. Blocking Behavior

### 8.1 When to Block
- Canonical object detected
- Target path ambiguous
- Write policy forbids action
- Multiple candidates conflict

### 8.2 Block Message Format

```
🚫 MUTATION BLOCKED

Object: {object_name}
Reason: {reason}
Action Attempted: {action}
Canonical Target: {resolved_path or "AMBIGUOUS"}
Policy: {write_policy}

Suggestion: {suggestion}
```

### 8.3 Block MUST NOT
- Silently fail
- Continue with fallback
- Create alternative file
- Guess target

---

## 9. Evidence Requirements

### 9.1 Required Evidence
Every mutation must log:
- `task_id`
- `object_name`
- `resolved_target`
- `write_policy`
- `decision` (allow|block)
- `reason`
- `consulted_sources`

### 9.2 Evidence Location
`artifacts/mutations/{task_id}_mutation_evidence.json`

---

## 10. Enforcement

### 10.1 Where Enforced
- `runtime/memory_preflight.py` - Preflight check
- Mutation executors - Gate integration
- Tool wrappers - Wrap write operations

### 10.2 Bypass Policy
**NO BYPASS ALLOWED for canonical objects.**

Non-canonical operations may proceed without full gate sequence.

---

## 11. Regression Tests

### 11.1 Required Tests
1. Existing canonical file → no duplicate created
2. Ambiguous resolution → blocked
3. update_only policy → create blocked
4. New session → same constraints

### 11.2 Test Location
`tests/test_mutation_guard.py`

---

## 12. Compliance

### 12.1 G3.5 Boundary
This policy is BUG FIX:
- ✅ Fixes blocking mainline bug
- ✅ No new features
- ✅ No multi-entry/multi-agent
- ✅ No full-on
- ✅ Enforces existing constraints

### 12.2 Non-Goals
- ❌ Expanding memory capabilities
- ❌ Adding new recall mechanisms
- ❌ Supporting multiple agents
- ❌ Full-on memory integration

---

## 13. Document Status

- ✅ Policy defined
- ✅ Gates specified
- ✅ Blocking behavior clear
- ✅ Evidence requirements set
- 🔜 Implementing enforcement

---

## 14. References

- Root Cause: `docs/memory/MEMORY_FAILURE_ROOT_CAUSE.md`
- Registry: `docs/memory/CANONICAL_OBJECT_REGISTRY.yaml`
- Implementation: `runtime/memory_preflight.py`
