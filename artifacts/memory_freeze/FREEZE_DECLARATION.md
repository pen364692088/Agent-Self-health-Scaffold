# Memory-LanceDB Freeze Declaration

Date: 2026-03-10 05:28 CST
Status: FROZEN
Baseline: Gate 1.7.7

---

## Frozen State

**No further modifications to memory capture main logic.**

### What is frozen:
- `shouldCapture()` function
- `extractRawUserText()` function
- `agent_end` hook capture logic
- Source guards and filters
- MEMORY_TRIGGERS patterns

### What is allowed:
- Bug fixes (critical only)
- Documentation updates
- Monitoring/logging improvements
- Performance optimizations (no behavior change)

### What requires explicit approval:
- New capture triggers
- Guard relaxation
- Policy changes
- Schema changes

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| Row count | 2 |
| autoCapture enabled | true |
| autoRecall enabled | true |
| embedding model | mxbai-embed-large |
| dimensions | 1024 |

---

## Observation Window

- Duration: 3-7 days
- Start: 2026-03-10 05:28 CST
- End: 2026-03-13 ~ 2026-03-17

---

## Metrics to Collect

1. **autoCapture hits**: Messages successfully captured
2. **recall injections**: Memories injected into context
3. **false captures**: Non-user content incorrectly captured
4. **duplicate/self-reinjected**: Wrapper content captured (should be 0)

---

## Exit Criteria

- No false captures
- No duplicate/self-reinjected memories
- autoCapture triggers on valid user preferences
- recall returns relevant results
- No regressions in other systems
