# CURRENT_STATUS.md

**Last Updated**: 2026-03-14
**Authority**: main_chain (ALL prompt/recovery decisions go through main_chain)

---

## Current Phase

**Phase 2.9: Prompt Limited Pilot Ready**

- Phase 2.0-2.6: ✅ COMPLETE (MaterializedState, CanonicalAdapter, PromptPreview, RecoveryPreview)
- Phase 2.7-2.8: ✅ COMPLETE (Promotion Gate passed with Grade A)
- Phase 2.9: ✅ DUAL GATE IMPLEMENTED (Ready for shadow mode)
- Phase 3: ❌ NOT STARTED

---

## Prompt Status

| Aspect | Status | Notes |
|--------|--------|-------|
| **Mode** | `DISABLED` | Ready to start shadow |
| **Authority** | `main_chain` | ALWAYS main_chain |
| **Shadow Systems** | ✅ Ready | MaterializedState + PromptPreview |
| **Pilot Scope** | Limited | recovery_success, task_ready_to_close, gate_completed |
| **Gate** | Dual Gate | 20 samples + 7 days max |

### Prompt Pilot Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| Shadow → Pilot | ≥20 samples, ≤7 days | ⏳ Waiting to start |
| Pilot → Decision | ≥30 samples, ≤14 days | Not applicable |

---

## Recovery Status

| Aspect | Status | Notes |
|--------|--------|-------|
| **Mode** | `SHADOW ONLY` | Never live |
| **Authority** | `main_chain` | ALWAYS main_chain |
| **Shadow Systems** | ✅ Ready | RecoveryPreview |
| **Live** | ❌ NEVER | Per explicit constraint |

---

## Capabilities Matrix

| Capability | Status | Mode |
|------------|--------|------|
| MaterializedState v0 | ✅ FROZEN | Read-only |
| CanonicalAdapter | ✅ COMPLETE | Shadow only |
| PromptPreview | ✅ COMPLETE | Shadow only |
| RecoveryPreview | ✅ COMPLETE | Shadow only |
| Prompt Pilot | ✅ READY | Dual gate, not started |
| Recovery Live | ❌ NOT ALLOWED | Explicitly forbidden |
| Phase 3 Kernel | ❌ NOT STARTED | Pending decision |

---

## Key Files

| File | Purpose |
|------|---------|
| `config/prompt_pilot.json` | Pilot configuration (authoritative) |
| `PHASE_2_9_DESIGN.md` | Dual gate design document |
| `docs/PROMPT_PILOT_RUNBOOK.md` | Operations runbook |
| `docs/MATERIALIZED_STATE_V0_SCOPE.md` | MaterializedState scope (frozen) |
| `README.md` | Project overview |

---

## Next Decision Point

**Current**: Pilot is DISABLED, ready to start shadow mode

**To Start Shadow**:
```bash
tools/prompt-pilot-preflight
tools/prompt-pilot-control --enable --mode shadow
```

**To Check Progress**:
```bash
tools/prompt-pilot-control --check-gate
tools/prompt-pilot-control --status
```

**To Switch to Pilot** (requires gate pass):
```bash
tools/prompt-pilot-control --set-mode pilot
```

---

## Constraints

| Constraint | Status |
|------------|--------|
| No handoff/capsule input | ✅ Enforced |
| No second live state | ✅ Enforced |
| No materialized_state authority | ✅ Enforced |
| No recovery live | ✅ Enforced |
| Final authority = main_chain | ✅ Enforced |

---

## Test Status

| Module | Tests | Status |
|--------|-------|--------|
| MaterializedState v0 | 30 | ✅ |
| CanonicalAdapter | 26 | ✅ |
| PromptPreview | 31 | ✅ |
| RecoveryPreview | 29 | ✅ |
| Phase 2.9 Validation | 7 | ✅ |
| **Total** | **123** | ✅ |
