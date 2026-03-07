# Shadow Observation Window - Start Record

**Window ID**: shadow-obs-001
**Start Time**: 2026-03-07 07:12 CST
**Status**: ACTIVE

## Configuration

**Mode**: Shadow (no real reply modification)
**Scope**: Low-risk sessions only
- single_topic_daily_chat
- non_critical_task
- simple_tool_context

**Excluded**:
- multi_file_debug
- high_commitment_task
- critical_execution
- multi_agent_collaboration

## Feature Flags

```
CONTEXT_COMPRESSION_ENABLED=1
CONTEXT_COMPRESSION_MODE=shadow
CONTEXT_COMPRESSION_BASELINE=new_baseline_anchor_patch
```

## Kill Switch

**File**: artifacts/context_compression/mainline_shadow/KILL_SWITCH.md
**Status**: INACTIVE (ready)

## Hook Status

**Hook**: context-compression-shadow
**Event**: message:preprocessed
**Enabled**: ✅ YES
**Eligible**: ✅ YES

## Target Metrics

### Core Chain Metrics
- budget_check_call_count
- sessions_evaluated_by_budget_check
- sessions_over_threshold
- compression_opportunity_count
- shadow_trigger_count
- retrieve_call_count

### Safety Metrics (must stay 0)
- real_reply_modified_count
- active_session_pollution_count

### Quality Metrics
- replay_guardrail (no degradation)
- continuity_signals (data collection)

## Observation Window Goals

1. **Primary**: Prove shadow path is exercised in production
2. **Secondary**: Collect compression opportunity data
3. **Tertiary**: Validate no pollution/side effects

## Exit Criteria

- [ ] budget_check_call_count > 10
- [ ] sessions_evaluated_by_budget_check > 10
- [ ] At least one shadow_trigger
- [ ] real_reply_modified_count = 0
- [ ] active_session_pollution_count = 0
- [ ] kill_switch not triggered

## Duration

**Target**: 3-7 days OR 50-100 sessions
**End Condition**: All exit criteria met

---

**Started**: 2026-03-07 07:12 CST
**Next Check**: 2026-03-08 07:12 CST (24h)
