# Config Alignment Incident

**Incident ID**: CAI-20260308-001
**Severity**: P1 (Config Alignment, not data corruption)
**Status**: DOCUMENTED
**Created**: 2026-03-08T00:17:00-06:00

---

## Summary

During Milestone B observation, discovered that `locked_config.json` records **expected** config, not **runtime actual** config.

### Runtime Truth (Observed)
```
contextWindow: 200000
trigger_type: threshold_92
before.ratio: 1.0209 (exceeded 200k)
after.ratio: 0.6125
```

### Documented Target (Expected)
```
max_tokens: 100000
threshold_enforced: 0.85
```

**Conclusion**: Runtime default is `200k / threshold_92`, not `100k / 0.85`.

---

## Impact

| Aspect | Impact |
|--------|--------|
| Evidence validity | Valid for runtime truth, not for target policy |
| Milestone B premise | Invalid - "default 100k" not true |
| Compression mechanism | Working correctly at runtime defaults |

---

## Decision

1. **Do NOT modify runtime config during observation**
2. **Accept runtime truth for current evidence chain**
3. **Split Milestone B into B1 (Runtime Truth) + B2 (Policy Compliance)**

---

## Milestone B Split

### B1: Runtime Truth Established ✅ DONE
- Current runtime config captured
- Natural trigger evidence preserved

### B2: Policy Compliance Validated ⏳ PENDING
- Requires proving `0.85 pre-assemble compression` works in production
- Requires config alignment or separate validation

---

## Files Created

- `CONFIG_ALIGNMENT_INCIDENT.md`
- `RUNTIME_DEFAULT_DISCOVERY.md`
- `runtime_config_snapshot.json`
- `natural_enforced_event_snapshot.json`

---

## Next Steps

1. Complete evidence chain with runtime truth
2. After observation freeze, decide on config alignment
3. If aligned to `100k / 0.85`, re-run full validation

---

*Incident documented: 2026-03-08T00:17:00-06:00*
