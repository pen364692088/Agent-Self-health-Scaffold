# RISKY_HISTORY_CANDIDATES.md

**Generated**: 2026-03-13
**Repository**: Agent-Self-health-Scaffold

## 🔴 CRITICAL: Secrets Exposed in Git History

### 1. Cerebras API Key

**File**: `cerebras_config.json`
**Commit**: `e2eb633 Archive: MVP11.4.5-11.4.8 complete...`
**Risk Level**: CRITICAL

**Exposed Secret**:
```json
"apiKey": "csk-txv2p9mkpe2dd86y38nr4wew3e66tmynt6hpyny8w2dxvpkd"
```

**Status**: 
- ✅ Removed from current tracking (tip)
- ⚠️ **Still present in git history**
- ⚠️ **Publicly accessible on GitHub**

**Required Action**:
1. **IMMEDIATE**: Rotate/Revoke the Cerebras API key
2. **REQUIRED**: History rewrite to remove the secret

---

## 🟡 MEDIUM: Telegram Session Traces in History

**Files**: `integrations/openclaw/traces/telegram:*.jsonl`
**Risk Level**: MEDIUM

**Content Found**:
- Telegram chat IDs (e.g., `telegram:8420019401`)
- Session identifiers
- Timestamps and message metadata

**History Evidence**:
```
+| 19:01:32 | Context Guard | pressure_check | agent:main:telegram:direct:8420019401 | telegram:8420019401 |
```

**Status**:
- ⚠️ Present in git history
- ⚠️ Contains PII (chat IDs)

**Recommended Action**: History rewrite recommended

---

## 🟡 MEDIUM: Session IDs in Logs

**Pattern Found**: `session_id`, `sessionId`, `runId` values in log files

**Example from history**:
```
+runId=ce2260c8
+runId=b4ad355b
+agent:main:telegram:direct:8420019401
```

**Risk Level**: MEDIUM
- Not credentials, but identifiable runtime state
- Could be used for correlation attacks

**Recommended Action**: History rewrite optional

---

## 🟢 LOW: Local Machine Paths

**Pattern Found**: Hardcoded paths like `/home/moonlight/...`

**Risk Level**: LOW
- Only reveals username and directory structure
- No security impact

**Recommended Action**: Tip cleanup sufficient

---

## Summary Table

| Finding | File | Risk | Tip Cleanup | History Rewrite |
|---------|------|------|-------------|-----------------|
| Cerebras API Key | cerebras_config.json | 🔴 CRITICAL | ✅ Done | **REQUIRED** |
| Telegram Chat IDs | traces/*.jsonl | 🟡 MEDIUM | ✅ Done | Recommended |
| Session IDs | logs/*.log | 🟡 MEDIUM | ✅ Done | Optional |
| Local paths | Various | 🟢 LOW | ✅ Done | Not needed |

---

## History Rewrite Requirements

### Immediate Action Required
1. **Rotate Cerebras API Key** at https://cloud.cerebras.ai
2. Do NOT push until key is rotated

### History Rewrite Scope
If proceeding with history rewrite:
- Target: `cerebras_config.json` (remove entirely from history)
- Tool: `git-filter-repo` (recommended)
- Impact: All contributors must re-clone

### Alternative (if history rewrite not feasible)
1. Rotate the API key immediately
2. Accept that the old key remains in history (but is now invalid)
3. Document the incident
