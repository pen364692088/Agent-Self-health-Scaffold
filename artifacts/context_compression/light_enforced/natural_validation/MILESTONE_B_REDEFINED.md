# Milestone B Redefined

**Updated**: 2026-03-08T00:17:00-06:00
**Reason**: Config Alignment Incident CAI-20260308-001

---

## Original Definition (Invalid)

"默认 100k 配置下自然触发验证"

**Invalidated because**: Runtime default is `200k`, not `100k`.

---

## New Definition

### Milestone B1: Runtime Truth Established ✅ DONE

**Purpose**: Document what the runtime default actually is.

**Pass Conditions**:
- [x] Runtime config snapshot captured
- [x] Natural enforced event observed
- [x] Evidence validity documented
- [x] Config gap identified

**Evidence**:
- `runtime_config_snapshot.json`
- `natural_enforced_event_snapshot.json`
- `RUNTIME_DEFAULT_DISCOVERY.md`

**Conclusion**:
- Runtime default: `200k / threshold_92`
- Compression works at runtime defaults
- Safety guardrails hold

---

### Milestone B2: Policy Compliance Validated ⏳ PENDING

**Purpose**: Prove target policy (`100k / 0.85`) is active in production.

**Pass Conditions**:
- [ ] Config aligned to `100k / 0.85` OR
- [ ] Separate validation shows `0.85` pre-assemble compression works
- [ ] Natural trigger at `0.85` observed
- [ ] Evidence preserved

**Blockers**:
- Current runtime does not enforce `0.85` threshold
- Config alignment required (separate gate)

**Dependencies**:
- Config Alignment Gate
- Re-run validation if config changed

---

## Status Update

| Milestone | Status | Evidence Location |
|-----------|--------|-------------------|
| B1 | ✅ DONE | `config_alignment/` |
| B2 | ⏳ PENDING | TBD |

---

## Key Insight

> The compression mechanism is correct. The config expectation was wrong.
> 
> B1 proves "it works at runtime defaults".
> B2 requires "it works at target policy".

---

*Milestone B redefined: 2026-03-08T00:17:00-06:00*
