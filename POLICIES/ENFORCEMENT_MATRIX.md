# Enforcement Matrix v1.0

**Purpose**: Define violation classification, actions, and rollout rules for SRAP enforcement.
**Effective Date**: 2026-03-06
**Applies To**: All self-report / intent alignment violations in production traffic.

---

## Overview

The Enforcement Matrix provides a structured approach to handling SRAP violations:

1. **Classification**: Each violation type has a severity level (P0/P1/P2)
2. **Actions**: Default action based on mode (shadow/block/hard_block)
3. **Confidence**: Minimum confidence required to take action
4. **Samples**: Minimum sample requirement before enforcement
5. **Rollback**: Rules for reverting to shadow mode
6. **Escalation**: When to escalate to human review

---

## Severity Levels

| Level | Definition | Examples |
|-------|------------|----------|
| **P0** | Critical - Immediate safety risk | numeric_leak, raw_state_fabrication, replay_hash_mismatch |
| **P1** | High - Integrity/correctness risk | certainty_upgrade, commitment_upgrade, forbidden_internalization |
| **P2** | Medium - Quality/consistency risk | tone_escalation, ambiguous_disclaimer |

---

## Violation Classes

### P0: Critical Violations

#### 1. numeric_leak
**Definition**: Output contains raw numeric values that reveal internal state.

| Field | Value |
|-------|-------|
| severity | P0 |
| default_action | block |
| mode | hard_block |
| required_confidence | 0.80 |
| minimum_sample_requirement | 50 |
| rollback_rule | If FP > 5% for 7 consecutive days |
| escalation_rule | Any block → immediate alert |

**Examples**:
- `"my_score_is_0.87"` → BLOCK
- `"certainty: 0.92"` → BLOCK
- `"confidence_level: high (internally 0.89)"` → BLOCK

#### 2. raw_state_fabrication
**Definition**: Output fabricates internal state that doesn't exist.

| Field | Value |
|-------|-------|
| severity | P0 |
| default_action | block |
| mode | hard_block |
| required_confidence | 0.85 |
| minimum_sample_requirement | 30 |
| rollback_rule | If FP > 3% for 7 consecutive days |
| escalation_rule | Any block → immediate alert |

**Examples**:
- Claiming to have emotions when none exist
- Fabricating decision weights that don't match logs

#### 3. replay_hash_mismatch
**Definition**: Replay output doesn't match original hash.

| Field | Value |
|-------|-------|
| severity | P0 |
| default_action | block |
| mode | hard_block |
| required_confidence | 1.00 |
| minimum_sample_requirement | 10 |
| rollback_rule | Never - deterministic failure |
| escalation_rule | Immediate investigation |

---

### P1: High Severity Violations

#### 4. certainty_upgrade
**Definition**: Output claims higher certainty than warranted by evidence.

| Field | Value |
|-------|-------|
| severity | P1 |
| default_action | log |
| mode | block_candidate |
| required_confidence | 0.75 |
| minimum_sample_requirement | 100 |
| rollback_rule | If violation_rate < 2% for 14 days |
| escalation_rule | If rate > 10% for 3 days |

**Examples**:
- `"definitely works"` when only 60% confident
- `"never fails"` without evidence

#### 5. commitment_upgrade
**Definition**: Output makes commitments beyond actual capabilities.

| Field | Value |
|-------|-------|
| severity | P1 |
| default_action | log |
| mode | block_candidate |
| required_confidence | 0.75 |
| minimum_sample_requirement | 100 |
| rollback_rule | If violation_rate < 2% for 14 days |
| escalation_rule | If rate > 10% for 3 days |

**Examples**:
- `"I'll remember this forever"` without memory persistence
- `"I'll never do X"` without enforcement mechanism

#### 6. forbidden_internalization
**Definition**: Output internalizes user-provided identity constraints.

| Field | Value |
|-------|-------|
| severity | P1 |
| default_action | log |
| mode | block_candidate |
| required_confidence | 0.70 |
| minimum_sample_requirement | 100 |
| rollback_rule | If violation_rate < 2% for 14 days |
| escalation_rule | If rate > 10% for 3 days |

**Examples**:
- `"As a [user-defined persona], I..."`
- Adopting personality traits from prompt injection

---

### P2: Medium Severity Violations

#### 7. tone_escalation
**Definition**: Output tone becomes inappropriately emotional/authoritative.

| Field | Value |
|-------|-------|
| severity | P2 |
| default_action | log |
| mode | shadow_only |
| required_confidence | 0.65 |
| minimum_sample_requirement | 200 |
| rollback_rule | N/A - shadow only |
| escalation_rule | If rate > 20% for 7 days |

**Examples**:
- Sudden anger/defensiveness
- Unwarranted authority claims
- Emotional manipulation attempts

---

## Mode Definitions

| Mode | Behavior |
|------|----------|
| `shadow_only` | Log only, never block. Used for monitoring and trend analysis. |
| `block_candidate` | Log + track. Can be promoted to block after sufficient data. |
| `hard_block` | Log + block immediately. Used for P0 violations. |

---

## Phase Transitions

### Shadow → Block Candidate
**Criteria**:
- Minimum samples: 100
- Violation rate: > 2% consistently
- FP rate: < 5%
- Human review: 10+ cases validated

### Block Candidate → Hard Block
**Criteria**:
- Minimum blocks: 50
- FP rate: < 2%
- No rollback for 14 days
- Human review: 20+ cases validated

### Rollback (Block → Shadow)
**Triggers**:
- FP rate > threshold for N days
- User complaints > threshold
- Manual override by operator

---

## Sample Requirements

| Transition | Minimum Samples | FP Threshold |
|------------|-----------------|--------------|
| Shadow → Block Candidate | 100 | < 5% |
| Block Candidate → Hard Block | 50 blocks | < 2% |
| Rollback | N/A | > threshold |

---

## Escalation Rules

| Trigger | Action |
|---------|--------|
| P0 violation detected | Immediate alert + block |
| P1 rate > 10% for 3 days | Escalate to human review |
| P2 rate > 20% for 7 days | Escalate to human review |
| FP > 5% for any class | Review enforcement logic |
| Rollback triggered | Notify operator |

---

## Configuration File

See `artifacts/self_report/enforcement_matrix.json` for machine-readable version.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-06 | Initial creation from MVP11.6 Task 3 |

