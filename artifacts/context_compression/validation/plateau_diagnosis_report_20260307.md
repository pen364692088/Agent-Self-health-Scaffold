# Plateau Diagnosis Report (Old-Topic)

Generated: 2026-03-07T02:43:45.434487

Mode: **old-topic plateau diagnosis** (read-only, no scoring/metrics/schema/baseline changes)

Total scorable old-topic samples analyzed: **30**
Current old_topic_recovery_on_scorable_samples: **0.51**

## 1) Score Distribution

| Band | Count |
|---|---:|
| 1.0 | 0 |
| 0.75-0.99 | 0 |
| 0.5-0.74 | 30 |
| 0.01-0.49 | 0 |
| 0.0 | 0 |

## 2) Read-only Diagnostic Labels (taxonomy)

| Label | Count |
|---|---:|
| correct_topic_wrong_anchor | 29 |
| topic_recalled_but_tool_state_missing | 8 |
| topic_recalled_but_constraint_stale | 4 |
| topic_recalled_but_open_loop_missing | 3 |
| topic_recalled_but_key_fact_missing | 1 |
| topic_recalled_only_after_user_nudge | 1 |

## 3) Sliced Performance

### by source_type
| source_type | samples | avg_old_topic_recovery |
|---|---:|---:|
| real_main_agent | 18 | 0.5 |
| historical_replay | 12 | 0.52 |

### by gap length
| gap_length | samples | avg_old_topic_recovery |
|---|---:|---:|
| medium | 6 | 0.5 |
| short | 24 | 0.51 |

### by with_open_loops overlap
| overlap | samples | avg_old_topic_recovery |
|---|---:|---:|
| no_open_overlap | 26 | 0.5 |
| with_open_loops | 4 | 0.55 |

### by user_correction overlap
| overlap | samples | avg_old_topic_recovery |
|---|---:|---:|
| no_user_correction_overlap | 26 | 0.51 |
| user_correction | 4 | 0.5 |

### by tool-context overlap
| overlap | samples | avg_old_topic_recovery |
|---|---:|---:|
| tool_context_none | 21 | 0.5 |
| tool_context_high | 8 | 0.53 |
| tool_context_low | 1 | 0.5 |

## 4) Bottom-5 Audit Summaries

### 1. sample_real_main_agent_old_topic_recall_4e781246
- source_type: real_main_agent
- bucket_tags: ['old_topic_recall']
- expected: Recover old topic with correct anchor, constraints, and open loops (target >=0.70)
- actual: old_topic_recovery=0.5, commitment_preservation=1.0
- missing piece: Key anchor fact (decision/ID/time) missing
- suspected root cause: topic matched but anchor selection weak

### 2. sample_real_main_agent_old_topic_recall_2a926844
- source_type: real_main_agent
- bucket_tags: ['old_topic_recall']
- expected: Recover old topic with correct anchor, constraints, and open loops (target >=0.70)
- actual: old_topic_recovery=0.5, commitment_preservation=1.0
- missing piece: Key anchor fact (decision/ID/time) missing
- suspected root cause: topic matched but anchor selection weak

### 3. sample_real_main_agent_old_topic_recall_e90ff040
- source_type: real_main_agent
- bucket_tags: ['old_topic_recall']
- expected: Recover old topic with correct anchor, constraints, and open loops (target >=0.70)
- actual: old_topic_recovery=0.5, commitment_preservation=1.0
- missing piece: Key anchor fact (decision/ID/time) missing
- suspected root cause: topic matched but anchor selection weak

### 4. sample_real_main_agent_old_topic_recall_750683fa
- source_type: real_main_agent
- bucket_tags: ['old_topic_recall']
- expected: Recover old topic with correct anchor, constraints, and open loops (target >=0.70)
- actual: old_topic_recovery=0.5, commitment_preservation=1.0
- missing piece: Key anchor fact (decision/ID/time) missing
- suspected root cause: topic matched but anchor selection weak

### 5. sample_real_main_agent_old_topic_recall_1301849c
- source_type: real_main_agent
- bucket_tags: ['old_topic_recall']
- expected: Recover old topic with correct anchor, constraints, and open loops (target >=0.70)
- actual: old_topic_recovery=0.5, commitment_preservation=1.0
- missing piece: Key anchor fact (decision/ID/time) missing
- suspected root cause: topic matched but anchor selection weak

## 5) Interpretation (read-only)

- Plateau near ~0.51 is primarily consistent with **correct topic but weak anchor/tool-state binding** rather than complete recall failure.
- Historical replay volume is no longer zero; remaining bottleneck appears to be **anchor fidelity** and **open-loop/tool-state carryover** quality.
- This report is diagnostic only and does not declare Gate 1 PASS/FAIL.