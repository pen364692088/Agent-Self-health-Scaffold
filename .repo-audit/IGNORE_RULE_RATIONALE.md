# IGNORE_RULE_RATIONALE.md

**Generated**: 2026-03-13
**Repository**: Agent-Self-health-Scaffold

## Summary
Updated `.gitignore` with comprehensive rules to prevent future pollution.

---

## Rule Categories and Rationale

### 1. Sensitive Config Files
```gitignore
cerebras_config.json
```
**Why**: Contains API keys/secrets
**Collaboration Impact**: None - each developer should use their own
**Source Code Risk**: None

### 2. Runtime Lock Files
```gitignore
*.pid
*.lock
```
**Why**: Machine-specific process state; prevents concurrent access issues
**Collaboration Impact**: None - locks are local
**Source Code Risk**: None (but `uv.lock` should be tracked for dependencies - re-added if needed)

### 3. Session State
```gitignore
.last_session_id
```
**Why**: Local session tracking file
**Collaboration Impact**: None
**Source Code Risk**: None

### 4. Logs Directory
```gitignore
logs/
```
**Why**: All log files are runtime-generated; can grow large; contain machine-specific info
**Collaboration Impact**: None - logs are regenerated
**Source Code Risk**: None

### 5. Reports Directory
```gitignore
reports/
```
**Why**: Generated outputs from tools; not source material
**Collaboration Impact**: None - reports are regenerated
**Source Code Risk**: None

### 6. Processed Events
```gitignore
events/processed/
```
**Why**: Already-handled events are transient state
**Collaboration Impact**: None
**Source Code Risk**: None

### 7. Mailbox Outputs
```gitignore
mailbox/out/
```
**Why**: Delivered messages are runtime artifacts
**Collaboration Impact**: None
**Source Code Risk**: None

### 8. Session Archives
```gitignore
session-archives/
```
**Why**: Local session history
**Collaboration Impact**: None - each user has their own
**Source Code Risk**: None

### 9. State Directory
```gitignore
state/
```
**Why**: Runtime state that should be local
**Collaboration Impact**: None
**Source Code Risk**: None

### 10. Integration Traces
```gitignore
integrations/openclaw/traces/
```
**Why**: Contains PII (chat IDs, session IDs)
**Collaboration Impact**: None
**Source Code Risk**: None

### 11. Memory Runtime Files
```gitignore
memory/.bootstrap_state.json
memory/.dedup_cache.json
memory/.locks/
memory/daily_summaries.jsonl
# ... etc
```
**Why**: Local caches and indices; machine-specific
**Collaboration Impact**: None - caches are rebuilt
**Source Code Risk**: None

### 12. Artifacts Runtime Directories
```gitignore
artifacts/context_compression/sessions/
artifacts/openviking/archive/
artifacts/self_health/state/
# ... etc
```
**Why**: Generated runtime data; can be large; machine-specific
**Collaboration Impact**: None - regenerated on each run
**Source Code Risk**: None

### 13. Standard Exclusions
```gitignore
__pycache__/
.pytest_cache/
*.pyc
node_modules/
.idea/
.DS_Store
```
**Why**: Standard Python/Node/IDE generated files
**Collaboration Impact**: None
**Source Code Risk**: None

---

## Files KEPT Tracked

### Documentation in artifacts/
- `artifacts/*/IMPLEMENTATION_SUMMARY.md`
- `artifacts/*/README.md`
- `artifacts/shared_knowledge/`

### Configuration Templates
- `*.template` files
- `config/*.yaml` (non-sensitive)

### Source Code
- All `.py` files in `core/`, `openviking/`, `runtime/`, `tools/`, `tests/`

---

## Future Maintenance

When adding new runtime output directories:
1. Check if content is regenerated on each run
2. If yes, add to `.gitignore`
3. If it contains documentation/templates, keep tracked
