# Session Continuity Rollout Plan

**Version**: v1.1.1  
**Date**: 2026-03-07

---

## Rollout Layers

### Layer 1: DEFAULT-ON (Immediate)

| Scenario | Rationale |
|----------|-----------|
| Main agent sessions | Highest value, most context |
| Long sessions (>10 turns) | High context risk |
| Engineering tasks | Critical state to preserve |
| Handoff flows | Direct benefit |
| Gate A/B/C delivery | Tool chain integration |

**Action**: Enabled by default, no configuration needed.

---

### Layer 2: OBSERVED (After monitoring)

| Scenario | Rationale |
|----------|-----------|
| Sub-agents | Medium complexity |
| Medium tasks (5-10 turns) | Moderate context |
| Project collaboration | State useful but not critical |

**Action**: Enabled with monitoring, check for issues.

---

### Layer 3: OPTIONAL (Manual enable)

| Scenario | Rationale |
|----------|-----------|
| Light chat | Low state value |
| Short sessions (<5 turns) | Minimal context |
| Temporary Q&A | No persistent state |

**Action**: Available but not forced.

---

## Rollout Phases

### Phase 1: Core Integration (Current)
- ✅ AGENTS.md updated
- ✅ HEARTBEAT.md updated
- ✅ Default tools enabled
- ✅ Gate integration

### Phase 2: Observation (Days 1-7)
- Monitor recovery success rate
- Track uncertainty triggers
- Validate conflict resolution
- Check WAL growth

### Phase 3: Full Deployment (After Phase 2)
- Enable for all Layer 2 scenarios
- Extend to sub-agents
- Full production use

---

## Rollout Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Recovery success rate | > 95% | < 90% |
| Uncertainty trigger rate | < 10% | > 20% |
| Conflict trigger rate | < 5% | > 15% |
| WAL size growth | < 1MB/day | > 10MB/day |

---

## Rollout Status

**Current Phase**: Phase 1 - Core Integration  
**Current Mode**: GUARDED STABLE  
**Next Review**: 2026-03-14