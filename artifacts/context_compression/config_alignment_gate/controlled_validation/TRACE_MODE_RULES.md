# Trace Mode Rules for Phase C

**Locked**: 2026-03-08T03:24:00-06:00

---

## Automatic Trace Mode Switching

### Mode: Observe (ratio < 0.75)

**Current Mode**: ACTIVE (65%)
**Trace Granularity**: LOW (every 5 turns)
**Fields Captured**: ratio, estimated_tokens, pressure_level, turn

### Mode: Candidate (0.75 ≤ ratio < 0.85)

**Trigger**: ratio >= 0.75
**Trace Granularity**: HIGH (every turn)
**Fields Captured**: 
- ratio, estimated_tokens, pressure_level, turn
- compression_state, recommended_action
- distance_to_085, tokens_to_085
- state_transition_event

**Auto-Actions**:
- Log state transition: idle → candidate
- Increase trace frequency
- Verify state machine flow

### Mode: Trigger Capture (ratio >= 0.85)

**Trigger**: ratio >= 0.85
**Trace Granularity**: MAXIMUM (every operation)
**Fields Captured**:
- All candidate fields PLUS:
- guardrail_id, trigger_condition
- action_taken, execution_result
- capsule_id, compression_event_id
- pre_assemble_compliant
- safety_counters_snapshot

**Auto-Actions**:
- Log state transition: candidate → pending
- Capture counter_before.json
- Capture budget_before.json
- Prepare for event capture
- Monitor for executing state

---

## Execution Rules (Corrected)

### Phase Progression

```
0 - 0.75:    observe trace mode (current)
0.75 - 0.85: candidate trace mode (HIGH granularity)
>= 0.85:     trigger capture mode (MAXIMUM granularity)
post-compression: verify ratio 回落到 <0.75 安全区
```

### Key Milestones

**Milestone 1: 150k / 0.75**
- 进入 candidate zone
- 切换到 HIGH trace granularity
- 验证 compression_state: idle → candidate
- 开始监控 state transitions

**Milestone 2: 170k / 0.85**
- 触发 trigger capture mode
- **三件事必须同时成立**:
  1. 命中 guardrail 2A
  2. action_taken = forced_standard_compression
  3. 触发发生在 assemble 前
- 验证 pre_assemble_compliant = yes

**Milestone 3: Post-Compression**
- 验证 ratio 回落到安全区
- 理想: < 0.75
- Safety counters = 0

### Automatic Mode Switching

```
IF ratio >= 0.75 AND ratio < 0.85:
  MODE = candidate
  trace_granularity = HIGH
  log_state_transition("idle", "candidate")
  START monitoring state machine flow

IF ratio >= 0.85:
  MODE = trigger_capture
  trace_granularity = MAXIMUM
  log_state_transition("candidate", "pending")
  CAPTURE guardrail_2a_event
  VERIFY forced_standard_compression
  VERIFY pre_assemble_compliant = yes

IF compression_complete:
  VERIFY post_compression_ratio < 0.75
  VERIFY safety_counters_zero
```

---

## Current Status

```
ratio: 0.66 (observe zone)
mode: observe trace
next_milestone: 0.75 (candidate entry) ← 关键节点
distance: 0.09 (~18k tokens)
```

**当前状态**: 即将进入 candidate 观察段
**不是**: "快收尾"
**重点**: 真正的验证点从 0.75 才开始变得关键

---

## Next Actions

1. Continue context ramp to 0.75+
2. On reaching 0.75: Switch to candidate trace mode
3. Continue to 0.85+
4. On reaching 0.85: Switch to trigger capture mode
5. Capture forced_standard_compression event
6. Verify pre_assemble_compliant = yes
7. Complete evidence package

---

*Rules locked: 2026-03-08T03:24:00-06:00*
