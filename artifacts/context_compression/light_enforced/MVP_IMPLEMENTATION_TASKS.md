# MVP Implementation Priorities + Test Checklist

## Goal

Build the smallest useful memory/compression system for OpenClaw that can:
- preserve current task continuity
- detect context pressure
- compress history into structured capsules
- support later recall and rollout

This document defines the MVP scope, implementation order, data structures, state machine fields, and the first automated test set.

---

## 1. MVP scope

### In scope
1. Working Memory v1
2. budget_check + compression candidate state
3. Capsule Builder v1
4. Basic capsule recall trigger
5. Minimal admissibility rules for eval data
6. Core safety and continuity tests

### Out of scope for MVP
1. Prompt assemble anchor injection
2. Full Retrieval optimization / vector ranking overhaul
3. Cross-session state machine
4. Stable Memory write automation
5. High-risk rollout / general enforced rollout

---

## 2. Implementation priority

### P0 — Working Memory v1
Implement a structured Working Memory store that is read every turn and updated before prompt assembly.

#### Required fields
```json
{
  "task_goal": {
    "primary": "...",
    "secondary": ["..."],
    "updated_at": "2026-03-07T10:00:00-06:00"
  },
  "open_loops": [
    {
      "id": "loop_001",
      "description": "Fix session-index",
      "status": "open",
      "priority": "high",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "recent_commitments": [
    {
      "id": "commit_001",
      "text": "Run shadow observation after hook fix",
      "scope": "current_session",
      "status": "active",
      "created_at": "..."
    }
  ],
  "user_corrected_constraints": [
    {
      "id": "constraint_001",
      "original": "Enable immediately",
      "corrected": "Shadow first, enforced later",
      "reason": "Need safety validation",
      "created_at": "..."
    }
  ],
  "current_tool_state": {
    "tool_name": "context-retrieve",
    "status": "healthy",
    "summary": "L1 available, L2 optional",
    "updated_at": "..."
  },
  "recent_errors": [
    {
      "id": "err_001",
      "error_type": "integration_gap",
      "summary": "budget-check hook not wired into mainline",
      "status": "resolved",
      "created_at": "..."
    }
  ]
}
```

#### Rules
- `task_goal.primary` is single-value and required.
- `secondary` is optional but structured as a list.
- `open_loops` must be structured objects, not plain strings.
- `recent_commitments` should remain structured to support preservation tests.
- `user_corrected_constraints` must preserve both original and corrected value.
- `current_tool_state` is a compact summary, not raw logs.
- `recent_errors` should keep only recent relevant issues, not full history.

#### Acceptance
- Working Memory loads every turn.
- Working Memory updates before prompt assembly.
- High-priority open loops survive multiple turns.
- User-corrected constraints overwrite older versions in the active view.

---

### P1 — budget_check + compression candidate state
Implement budget estimation and compression-state transitions.

#### budget_check output
```json
{
  "estimated_tokens": 45000,
  "max_tokens": 100000,
  "ratio": 0.45,
  "pressure_level": "moderate",
  "budget_band": "safe",
  "threshold_hit": null,
  "recommended_action": "continue",
  "evaluated_at": "2026-03-07T10:03:00-06:00"
}
```

#### Required fields
- `estimated_tokens`
- `max_tokens`
- `ratio`
- `pressure_level`
- `budget_band`
- `threshold_hit`
- `recommended_action`
- `evaluated_at`

#### Budget bands
- `safe`: ratio < 0.75
- `candidate`: 0.75 <= ratio < 0.85
- `standard_compress`: 0.85 <= ratio < 0.92
- `strong_compress`: ratio >= 0.92

#### compression_state values
- `idle`
- `candidate`
- `pending`
- `executing`
- `completed`
- `failed`

#### Transition rules
- `idle -> candidate` when ratio enters candidate band or semantic boundary score passes threshold.
- `candidate -> pending` when next-turn check remains high or ratio >= 0.85.
- `pending -> executing` immediately before prompt assembly.
- `executing -> completed` on successful capsule commit and trim.
- `executing -> failed` on compression error.
- `failed -> idle` only after fallback/logging completes.

#### Acceptance
- budget_check runs before prompt assembly.
- candidate state is visible in session state.
- ratio >= 0.85 forces compression this turn.
- failures are logged and recoverable.

---

### P2 — Capsule Builder v1
Implement the first structured compression artifact.

#### Minimum capsule fields
```json
{
  "capsule_id": "cap_0001",
  "topic_key": "context-compression",
  "decision_anchor": "Run shadow before light enforced",
  "constraint_anchor": ["Do not modify baseline", "Low-risk only"],
  "open_loop_anchor": ["Collect 50+ sessions", "Re-run readiness check"],
  "entity_anchor": ["context-budget-check", "context-compress"],
  "created_at": "2026-03-07T10:10:00-06:00",
  "source_turn_range": {
    "start_turn": 41,
    "end_turn": 57,
    "start_msg_id": "optional_msg_start",
    "end_msg_id": "optional_msg_end"
  }
}
```

#### source_turn_range rule
Use `start_turn` + `end_turn` as the primary tracing format.
Optional `start_msg_id` / `end_msg_id` may be added when available.
Do not use only `turn_count`.

#### Anchor presence rule
- `topic_key` is required.
- Other anchors are optional.
- Store values only when present.
- Also store presence metadata if needed for debugging/eval.

Example:
```json
{
  "anchor_presence": {
    "decision_anchor": "present",
    "constraint_anchor": "present",
    "open_loop_anchor": "present",
    "entity_anchor": "present",
    "time_anchor": "absent",
    "tool_state_anchor": "unknown"
  }
}
```

#### Acceptance
- Capsule can be generated from a completed subtopic or compression event.
- Capsule always contains `topic_key`.
- Capsule preserves at least one high-value anchor.
- Capsule retains traceability to original turns.

---

### P3 — Basic capsule recall
Use capsule recall before deep retrieval.

#### Trigger conditions
Recall capsule when one or more hold:
- user returns to an old topic
- current query hits prior decision/entity/open loop
- Working Memory is insufficient for continuity
- previous stage context is needed for answer quality

#### Basic ranking
Sort candidates by:
1. decision overlap
2. constraint overlap
3. open_loop overlap
4. entity overlap
5. time proximity
6. topic match

#### Acceptance
- old-topic follow-up can retrieve a relevant capsule
- retrieved capsule is fused into Working Memory facts, not dumped raw into prompt

---

## 3. Mainline integration points

Use this order inside the OpenClaw mainline:

1. receive message
2. load bootstrap files
3. read Stable minimal + Working Memory
4. update Working Memory from current event
5. run budget_check
6. run lightweight semantic boundary detection
7. if needed: generate capsule / trim history
8. if needed: recall capsule / retrieval and fuse facts into Working Memory
9. assemble prompt
10. call LLM
11. run tools
12. write back state updates

### Important rule
Compression and recall decisions must happen **before** prompt assembly.
State write-back happens **after** LLM/tool completion.

---

## 4. Lightweight semantic boundary detection

### MVP choice
Use **rule-based detection + heuristic scoring**.
Do not add a dedicated model in MVP.

### Signals
- topic shift
- stage closure
- constraint correction
- redundancy increase

### Example score
```text
boundary_score =
  topic_shift_score +
  closure_score +
  correction_score +
  redundancy_score
```

Enter `Compression Candidate` when:
- score passes threshold, or
- budget ratio enters candidate band

---

## 5. Session-state persistence

### MVP decision
Use a **session-local state machine**.
Persist state in the session state file, with hot values optionally cached in memory.

### Persist at least
- compression_state
- recall_state
- last_topic_key
- recent_budget_band
- active_open_loops_count
- last_compression_at
- last_recall_at
- working_memory_snapshot_ref
- capsule_refs

Do not build a cross-session state machine in MVP.

---

## 6. Capsule sinking rule (post-MVP-ready design note)

Not required for MVP implementation, but define direction early.

Sink a capsule toward Retrieval when one or more apply:
- capsule count exceeds threshold
- age exceeds threshold
- not recalled for N turns
- topic is clearly closed
- a newer capsule supersedes it

Retain a light pointer:
```json
{
  "capsule_id": "cap_1024",
  "topic_key": "context-compression",
  "anchor_digest": {
    "decision_anchor": "keep S1 freeze",
    "entity_anchor": ["OpenViking"],
    "open_loop_anchor": "fix session-index"
  },
  "retrieval_id": "ret_8fd3",
  "archive_status": "sunk"
}
```

---

## 7. MVP test checklist

## P0 — Safety and integrity

### T1. Real reply unchanged in shadow path
- hook runs
- counters grow
- real reply remains unchanged

### T2. Active session not polluted
- no shadow result leaks into active session state incorrectly

### T3. Kill switch works
- disable compression path instantly
- mainline continues safely

### T4. Stable memory not polluted by short-term noise
- temporary session detail does not overwrite stable rules

---

## P1 — Continuity and compression correctness

### T5. Compression continuity test
Given a long session, after compression the system can still answer follow-up questions about the same topic.

### T6. Open loop preservation
Compression keeps high-priority open loops.

### T7. Constraint preservation
Compression keeps corrected constraints and does not regress to older ones.

### T8. Old-topic recall
System can reconnect to a prior topic using capsule recall.

---

## P2 — Anchor precision

### T9. correct_topic_wrong_anchor regression test
The system distinguishes different instances within the same topic.

### T10. Decision anchor recall
Decision context is preserved and recalled correctly.

### T11. Entity/tool-state recall
Technical sessions recover correct module/tool context.

---

## P3 — Boundary and archive behavior

### T12. Capsule sinking test
Older capsule can sink without destroying recoverability.

### T13. Retrieval non-overuse test
Deep retrieval is not called when Working + Capsule is enough.

### T14. Invalid sample isolation
Heartbeat-only / empty-text samples are excluded from benchmark-critical evaluation.

---

## P4 — Integration and performance

### T15. Hook exercise test
budget_check / compress / retrieve hooks are actually called in mainline.

### T16. Trigger readiness test
Low-risk long session can reach over-threshold and real trigger.

### T17. Latency sanity test
Lightweight main loop remains within acceptable latency bounds.

---

## 8. Recommended implementation order

### Phase 1
- Working Memory v1
- session state persistence
- budget_check output and compression_state transitions

### Phase 2
- Capsule Builder v1
- boundary scorer
- pre-assemble compression decision

### Phase 3
- basic capsule recall
- anchor-aware candidate ranking
- continuity tests

### Phase 4
- archive/sink mechanics
- retrieval fallback
- integration hardening

---

## 9. Definition of done for MVP

MVP is considered complete when all conditions below are true:

1. Working Memory is updated/read every turn
2. budget_check runs before prompt assembly
3. compression_state is persisted and transitions correctly
4. Capsule Builder v1 generates traceable capsules
5. old-topic follow-up can use capsule recall
6. P0 safety tests pass
7. P1 continuity tests pass
8. mainline hook exercise is verified

---

## 10. One-line principle

Working Memory holds what matters now; budget_check decides when pressure is rising; Capsule v1 preserves structured continuity; recall must fuse facts back into Working Memory instead of dumping raw history into prompt.
