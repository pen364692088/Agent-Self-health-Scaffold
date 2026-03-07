# Patch Set Freeze Declaration

**Version**: 1.0
**Frozen At**: 2026-03-07T04:30:00CST
**Status**: FROZEN

---

## Purpose

Declare the fixed patch set for new baseline validation. This patch set will NOT be modified during the validation period.

---

## Included Patches

### 1. Anchor-Enhanced Capsule Builder

**Version**: 1.0
**File**: `run_candidate_validation.py` (embedded)

**Function**:
- Extracts anchors from conversation events
- Anchor types: decision, entity, time, open_loop, constraint, tool_state
- Returns structured anchor list with confidence scores

**Extraction Patterns**:
```yaml
decision:
  - 决定, 确认, 选择, 采用
  - decide, confirmed, ✅, completed

entity:
  - files (*.py, *.js, *.ts, *.json, *.md, etc.)
  - tools, commands

open_loop:
  - TODO, TBD, 待定, pending
  - need to, 待处理

constraint:
  - 必须, 不能, 禁止
  - must, cannot, forbidden

tool_state:
  - 执行, 运行, 调用
  - executed, ran, called
```

---

### 2. Anchor-Aware Retrieve

**Version**: 1.0
**File**: `run_candidate_validation.py` (embedded)

**Function**:
- Ranks retrieval results by anchor coverage
- Applies weighted scoring
- Returns final score (0-1)

**Weights**:
```yaml
decision: 0.25
entity: 0.20
time: 0.15
open_loop: 0.20
constraint: 0.15
tool_state: 0.05
```

**Bonuses**:
- Anchor diversity: +0.08 per anchor type present
- Open loop match: +0.15
- Tool context match: +0.10

---

### 3. Admissibility Policy

**Version**: 1.0
**File**: `artifacts/context_compression/anchor-binding/ADMISSIBILITY_POLICY.md`

**Function**:
- Filters heartbeat-only samples
- Ensures minimum content quality
- Separates admissible vs not_admissible

**Rules**:
```yaml
min_user_messages: 2
min_assistant_messages: 2
min_text_length: 500
min_anchor_types: 2
exclude_heartbeat_only: true
```

---

## Explicitly Excluded

The following are **NOT** included in this patch set:

| Component | Reason |
|-----------|--------|
| Prompt Assemble Anchor Injection | Not needed - retrieve alone sufficient |
| Scoring Formula Changes | Keep compatibility with existing metrics |
| Metrics Formula Changes | Keep compatibility with existing dashboard |
| Schema Mainline Changes | No schema modifications required |
| Other Experimental Optimizations | Scope control |

---

## Modification Policy

**This patch set is FROZEN.**

Any modification requires:
1. Explicit approval from validation lead
2. Version bump to 1.1
3. Re-validation of all samples
4. Update to BASELINE_MANIFEST.json

---

## Relationship to Old S1 Baseline

| Aspect | Old S1 | New Baseline |
|--------|--------|--------------|
| Manifest | S1_BASELINE_MANIFEST.json | BASELINE_MANIFEST.json (this) |
| Status | FROZEN | FROZEN |
| Gate 1 | BLOCKED | Not applicable |
| Conclusion | anchor-binding plateau | Parallel validation |
| Inheritance | None | None |

**No back-writing to old S1 is allowed.**

---

## Validation Mode

```yaml
mode: shadow
isolation: full
main_pipeline: NOT connected
active_session: NOT modified
```

---

**Keywords**: `patchset-freeze` `new-baseline` `validation-frozen`
