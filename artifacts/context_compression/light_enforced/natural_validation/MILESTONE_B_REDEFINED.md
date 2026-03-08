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

### Milestone B2: Policy Compliance Validated ⏸️ WAITING FOR CONFIG ALIGNMENT GATE

**Purpose**: Prove target policy (`100k / 0.85`) is active in production.

**Status**: 未启动，等待 Config Alignment Gate 决策后再启动

**Pass Conditions**:
- [ ] Config aligned to `100k / 0.85` OR
- [ ] Separate validation shows `0.85` pre-assemble compression works
- [ ] Natural trigger at `0.85` observed
- [ ] Evidence preserved

**Dependencies**:
- Config Alignment Gate (必须先通过)
- 如果配置变更，需要重新运行验证

**重要**:
- 不要把 B2 标记为"进行中验证"
- B1 观察结果不能用于证明目标策略有效
- 当前证据仅对 runtime truth（200k / 0.92）有效

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
