# Context Compression - Final Documentation Block

## Complete System Reference

### System Overview

The context compression system automatically manages token usage in OpenClaw sessions, preventing context overflow while preserving critical information through structured capsule summaries.

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Threshold | 0.85 | Pending |
| Latency | < 500ms | TBD |
| Success Rate | > 99% | TBD |
| Safety | 0 violations | Active |

### Configuration Values

```
Context Window: 200k tokens
Enforced Threshold: 0.85
Strong Threshold: 0.92
Mode: light_enforced
Critical Rule: 不允许跨过 0.85 后继续拖延
```

### Validation Status

- [x] Configuration verified
- [x] Tools tested
- [x] Evidence directory ready
- [ ] Candidate zone reached
- [ ] Trigger zone reached
- [ ] Compression captured
- [ ] Evidence complete

### Next Actions

1. Reach 0.75 candidate zone
2. Switch to HIGH trace mode
3. Continue to 0.85 trigger zone
4. Capture guardrail event
5. Verify compression success
6. Complete evidence package

---

## Final System Checklist

### Pre-Candidate

- [x] Context at 72%
- [x] State: idle
- [x] Mode: observe trace
- [x] Ready for candidate entry

### At Candidate (0.75)

- [ ] State: candidate
- [ ] Mode: HIGH trace
- [ ] Transition logged
- [ ] Monitoring active

### At Trigger (0.85)

- [ ] State: pending
- [ ] Mode: MAX trace
- [ ] Guardrail 2A: yes
- [ ] Evidence capture: started

### Post-Compression

- [ ] State: completed
- [ ] Ratio: < 0.75
- [ ] Safety: zero
- [ ] Evidence: complete

---

**End of Documentation**
