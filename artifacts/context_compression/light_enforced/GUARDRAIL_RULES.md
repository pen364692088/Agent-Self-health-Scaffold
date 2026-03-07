# GUARDRAIL_RULES.md

## Goal

Define a practical guardrail system for a hybrid memory architecture with four layers:
- Stable Memory
- Working Memory
- Capsule Memory
- Retrieval Memory

The purpose of these guardrails is to prevent the most common systemic failures during:
- compression
- recall
- memory promotion
- mainline integration

This document focuses on five core failure modes and specifies for each:
1. trigger conditions
2. actions
3. monitoring metrics

---

## Failure Mode 1: Compression Too Early

### Problem
Compression happens before the context has semantically matured.
This causes loss of in-progress decisions, open loops, or recent constraint corrections.

### Typical symptoms
- discussion is still evolving, but gets compressed into an over-general capsule
- a decision is still being revised, but is recorded as final
- open loops are lost before they are stabilized

---

### Guardrail 1A: Immature Branch Block

#### Trigger conditions
Block or downgrade compression when any of the following are true:
- a new `decision` revision appears within the last `N` turns
- `open_loops` increased within the last `N` turns
- `constraint` was corrected within the last `N` turns
- the same topic remains highly active across the last 3 turns
- current tool state is still `running`, `partial`, or `unresolved`

#### Action
- block standard compression
- allow only light compression if budget pressure exists
- mark current topic branch as `immature_branch=true`
- preserve high-value anchors in Working Memory

#### Monitoring metrics
- `early_compression_block_count`
- `immature_branch_ratio`
- `post_compression_decision_regret_count`
- `open_loop_lost_after_compress_count`

---

### Guardrail 1B: Maturity Score Gate

#### Trigger conditions
Compute `maturity_score` from signals such as:
- explicit phase conclusion present
- at least one open loop stabilized or closed
- low novelty / high repetition in recent turns
- no recent decision revision

#### Action
- if `maturity_score < threshold`, do not commit a final capsule
- create `candidate_capsule_draft` only
- defer full compression to a later turn or boundary

#### Monitoring metrics
- `capsule_draft_to_commit_ratio`
- `maturity_score_distribution`
- `capsule_regeneration_rate`

---

## Failure Mode 2: Compression Too Late

### Problem
Compression is delayed until context pressure is already extreme.
The system is then forced into coarse compression or truncation.

### Typical symptoms
- compression only starts at 0.95 budget ratio
- anchor extraction degrades under pressure
- system falls back to soft truncation and loses continuity

---

### Guardrail 2A: Hard Threshold Enforcement

#### Trigger conditions
- `budget_ratio >= 0.85` -> compression must run before prompt assembly
- `budget_ratio >= 0.92` -> strong compression mode

#### Action
- 0.85–0.92: standard compression
- >=0.92: strong compression
- if compression fails, create emergency anchor-preserving fallback

#### Monitoring metrics
- `late_compression_count`
- `ratio_over_085_turns`
- `ratio_over_092_turns`
- `forced_strong_compression_count`

---

### Guardrail 2B: Candidate Stall Alert

#### Trigger conditions
- `Compression Candidate` persists for more than `M` turns
- or `budget_ratio >= 0.85` persists for `N` turns

#### Action
- emit internal alert
- force compression on next eligible turn
- mark `compression_delay_violation=true`

#### Monitoring metrics
- `candidate_stall_turns`
- `compression_delay_violation_count`
- `avg_ratio_before_compress`

---

### Guardrail 2C: Emergency Anchor Preservation

#### Trigger conditions
- strong compression mode entered
- or compression failed under high pressure

#### Action
Before any fallback truncation, preserve at least:
- `decision`
- `constraint`
- `open_loop`
- `entity`
- `tool_state`

Store them in an `emergency_capsule` or equivalent fallback structure.

#### Monitoring metrics
- `emergency_capsule_count`
- `anchor_preservation_under_pressure_rate`

---

## Failure Mode 3: Recall Hits Topic but Misses Anchor

### Problem
The system recalls the right general topic but the wrong concrete instance.

### Typical symptoms
- user asks about a previous bug fix
- system recalls a bug-fix capsule from the wrong case
- topic is correct, anchor is wrong

---

### Guardrail 3A: Anchor-Aware Ranking Required

#### Trigger conditions
- multiple recall candidates share the same `topic_key`
- or one topic has multiple plausible historical instances

#### Action
Ranking must include anchor overlap, not just topic match:
- `decision overlap`
- `constraint overlap`
- `open_loop overlap`
- `entity overlap`
- `tool_state continuity`
- `time proximity`

#### Monitoring metrics
- `correct_topic_wrong_anchor_count`
- `anchor_disambiguation_invocations`
- `top1_top2_margin_distribution`

---

### Guardrail 3B: Low-Margin Recall Downgrade

#### Trigger conditions
- `top1_top2_margin < epsilon`
- or too many anchor fields are missing

#### Action
- do not directly commit recall into Working Memory
- store as `tentative_recall`
- optionally request clarification
- avoid high-confidence overwrite

#### Monitoring metrics
- `tentative_recall_count`
- `clarification_needed_count`
- `low_margin_recall_rate`

---

### Guardrail 3C: Capsule Instance Quality Audit

#### Trigger conditions
- too many capsules under the same `topic_key`
- repeated anchor confusion for the same topic

#### Action
- audit capsule anchor quality
- down-rank low-quality capsules
- mark weak capsules as lower-trust recall candidates

#### Monitoring metrics
- `duplicate_topic_capsule_count`
- `low_anchor_quality_capsule_count`

---

## Failure Mode 4: Working Memory Polluted by Bad Recall

### Problem
A mistaken historical recall is written back into Working Memory and distorts future reasoning.

### Typical symptoms
- wrong historical decision is treated as current fact
- bad recall overwrites active constraints or open loops
- downstream replies drift for several turns

---

### Guardrail 4A: Tentative Before Commit

#### Trigger conditions
Any recall result that is about to update Working Memory.

#### Action
Recall must first enter tentative fields, for example:
- `tentative_recalled_decision`
- `tentative_recalled_constraint`
- `tentative_recalled_open_loop`

Only promote to committed if:
- anchor confidence is high
- there is no Working Memory conflict
- current query strongly supports the recall

#### Monitoring metrics
- `tentative_recall_count`
- `tentative_to_committed_rate`
- `tentative_recall_rejection_count`

---

### Guardrail 4B: Conflict Detector

#### Trigger conditions
Recall result overlaps with any current Working Memory field:
- `task_goal`
- `constraint`
- `open_loop`
- `recent_commitments`
- `tool_state`

#### Action
If conflict exists:
- do not overwrite current Working Memory
- mark `recall_conflict=true`
- store in conflict bucket or tentative layer
- optionally request clarification

#### Monitoring metrics
- `recall_conflict_count`
- `conflict_by_field`
- `wrong_recall_writeback_count`

---

### Guardrail 4C: Writeback Permission Tiers

#### Trigger conditions
Recall result classified by confidence and conflict status.

#### Action
- high confidence + no conflict -> committed writeback allowed
- medium confidence or light conflict -> tentative only
- low confidence or strong conflict -> blocked writeback

#### Monitoring metrics
- `committed_recall_count`
- `tentative_only_recall_count`
- `blocked_recall_write_count`

---

## Failure Mode 5: Stable Memory Eroded by Short-Term Noise

### Problem
Temporary state, mood, or single-session details get promoted into long-term stable memory.

### Typical symptoms
- one-off emotional statement becomes a long-term preference
- temporary project state is treated as permanent policy
- noisy single-session detail becomes stable behavior rule

---

### Guardrail 5A: Promotion Gate

#### Trigger conditions
A memory candidate is proposed for Stable Memory.

#### Action
Only allow promotion if the candidate satisfies most or all of:
- repeated across multiple sessions or time points
- clearly belongs to preference / rule / long-term constraint class
- remains valid beyond the current task
- is not temporary state or emotion

Otherwise:
- store in `stable_candidate_pool`
- do not directly commit to Stable Memory

#### Monitoring metrics
- `stable_candidate_count`
- `stable_promotion_rate`
- `candidate_expiry_rate`

---

### Guardrail 5B: Type Whitelist

#### Trigger conditions
Any attempt to write to Stable Memory.

#### Action
Allow only:
- long-term preferences
- fixed protocol rules
- identity constraints
- long-term behavior boundaries

Reject:
- temporary mood
- one-off task state
- single incident errors
- heartbeat / keepalive / empty events
- short-lived environmental details

#### Monitoring metrics
- `stable_write_rejected_by_type_count`
- `stable_write_type_distribution`

---

### Guardrail 5C: Drift Audit

#### Trigger conditions
Run on schedule (daily / per phase / per rollout checkpoint).

#### Action
Audit whether recent Stable writes:
- came mostly from a single session
- resemble short-term noise
- conflict with older stable entries

If drift is suspected:
- rollback or downgrade recent entries
- mark `stable_drift_suspected=true`

#### Monitoring metrics
- `stable_drift_alert_count`
- `stable_rollback_count`
- `single_session_promotion_count`

---

## Unified Guardrail Action Levels

For implementation simplicity, all guardrails should map to one of three action levels:

### 1. Block
Use when risk is high.
Examples:
- block compression
- block writeback
- block Stable promotion

### 2. Warn / Degrade
Use when risk is moderate.
Examples:
- light compression only
- tentative recall only
- keep candidate in pending pool

### 3. Monitor
Use when the system is still safe but a trend may be emerging.
Examples:
- counter only
- audit later
- no immediate workflow change

---

## Unified Monitoring Dashboard

### Compression
- `early_compression_block_count`
- `late_compression_count`
- `forced_strong_compression_count`
- `compression_delay_violation_count`

### Recall
- `correct_topic_wrong_anchor_count`
- `recall_conflict_count`
- `tentative_to_committed_rate`
- `low_margin_recall_rate`

### Stable Memory
- `stable_candidate_count`
- `stable_promotion_rate`
- `stable_drift_alert_count`
- `stable_rollback_count`

### Safety
- `real_reply_corruption_count`
- `active_session_pollution_count`
- `rollback_event_count`

---

## Core Principles

1. Compression must not run ahead of semantic maturity.
2. Compression must not be delayed until quality collapses.
3. Recall must not rely on topic-only matching.
4. Recall must not directly overwrite Working Memory without validation.
5. Stable Memory must not accept short-term noise as long-term truth.

---

## Definition of Success

This guardrail system is considered minimally effective when:
- early compression is blocked before key open loops are lost
- late compression no longer forces uncontrolled truncation
- `correct_topic_wrong_anchor` drops substantially
- bad recall no longer pollutes Working Memory directly
- Stable Memory promotion becomes rare, explicit, and auditable

