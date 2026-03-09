# Decision Context Schema

## Purpose

定义 `decision_context` 信号的提取标准，使其成为可度量、可验证的恢复质量增强器。

---

## Definition

**decision_context** = 最近一次明确决策及其依据

它回答的问题是：
> **"为什么选择这个方案/路径？做决策时的权衡是什么？"**

---

## Signal vs Other Signals

| Signal | Answers | Example |
|--------|---------|---------|
| topic | "我们在做什么？" | "实现 Context Compression Pipeline" |
| task_active | "任务是否仍在进行？" | "是，正在校准 evaluator" |
| next_action | "下一步做什么？" | "运行 shadow validation" |
| tool_state | "工具当前状态？" | "已调用 capsule-builder 3 次" |
| **decision_context** | **"为什么选这个方案？"** | **"采用 gate-based scoring 因为阈值法 FP 太高"** |

**Key Distinction**:
- `next_action` = WHAT to do next
- `decision_context` = WHY we chose this path

---

## Extraction Patterns

### Pattern 1: Explicit Decision Markers

Keywords indicating a decision was made:
- "决定/采用/选择/改为/切换到"
- "结论是/最终方案/选定"
- "因为...所以..."
- "原因/根因/出于...考虑"

**Example**:
```
Input: "经过对比，我们决定采用 gate-based scoring，
因为阈值法在 stress test 中 FP 率太高。"

Extracted decision_context:
{
  "decision": "采用 gate-based scoring",
  "rationale": "阈值法 FP 率太高",
  "alternatives_rejected": ["阈值法"]
}
```

### Pattern 2: Trade-off / Trade-off Resolution

Keywords:
- "权衡/取舍/代价/代价是"
- "虽然...但是..."
- "优先考虑/牺牲...换取..."

**Example**:
```
Input: "虽然 V2 实现复杂度更高，但它提供了更好的可解释性，
权衡后决定继续使用 V2。"

Extracted decision_context:
{
  "decision": "继续使用 V2",
  "rationale": "更好的可解释性",
  "trade_off": {
    "accepted_cost": "实现复杂度更高",
    "benefit_gained": "更好的可解释性"
  }
}
```

### Pattern 3: Problem-Solution Link

Keywords:
- "为了解决...问题"
- "针对...采用..."
- "修复/解决/处理后"

**Example**:
```
Input: "为了解决 long_technical 的 FP 问题，
我们在 rubric 中增加了 decision_context 权重。"

Extracted decision_context:
{
  "decision": "增加 decision_context 权重",
  "rationale": "解决 long_technical FP 问题",
  "problem_addressed": "long_technical FP"
}
```

### Pattern 4: Branch / Path Selection

Keywords:
- "方案A/方案B"
- "分支/路径/选项"
- "最终选择了/没有选择"

**Example**:
```
Input: "我们评估了方案A（重写evaluator）和方案B（增加信号提取），
最终选择方案B，因为改动范围更可控。"

Extracted decision_context:
{
  "decision": "选择方案B（增加信号提取）",
  "rationale": "改动范围更可控",
  "alternatives_evaluated": [
    {"option": "方案A（重写evaluator）", "rejected_reason": "未说明"},
    {"option": "方案B（增加信号提取）", "selected": true}
  ]
}
```

---

## Schema Definition

```json
{
  "decision_context": {
    "present": "boolean",
    "decisions": [
      {
        "decision": "string - 做了什么决策",
        "rationale": "string - 为什么做这个决策",
        "timestamp_hint": "string|null - 决策发生的大致时间/位置",
        "alternatives_rejected": ["string"],
        "trade_off": {
          "accepted_cost": "string",
          "benefit_gained": "string"
        }
      }
    ],
    "current_strategy": "string|null - 当前采用的策略/方案",
    "open_decisions": ["string - 仍需决策的事项"],
    "extraction_confidence": "float (0-1)"
  }
}
```

---

## Minimum Viable Extraction

For Phase D, focus on **single most recent decision**:

```json
{
  "decision_context": {
    "present": true,
    "last_decision": {
      "what": "采用 gate-based scoring",
      "why": "阈值法 FP 太高"
    }
  }
}
```

This is sufficient to differentiate:
- **With decision_context**: Knows WHY this path
- **Without decision_context**: Only knows WHAT to do

---

## Scoring Integration

### Option A: Hard Gate (Not Recommended)

```
if not decision_context.present:
    readiness *= 0.5  # Heavy penalty
```

**Risk**: Too aggressive, may hurt valid cases.

### Option B: Soft Enhancement (Recommended)

```
if decision_context.present:
    readiness += 0.1  # Small bonus
    completeness_score += 0.2
```

**Rationale**: Encourages extraction without blocking recovery.

### Option C: Completeness Tier

```
# Recovery Completeness Levels
level_1 (basic): topic + task + next_action
level_2 (enhanced): level_1 + tool_state
level_3 (complete): level_2 + decision_context

if decision_context.present:
    completeness_tier = "complete"
```

**Recommendation**: Start with Option B (soft enhancement).

---

## Validation Criteria

### True Positive
- Extracted text contains actual decision
- Rationale explains the "why"
- Not just background information

### False Positive
- General description without decision
- Background context without rationale
- Topic summary mistaken for decision

### Test Cases

| Input | Expected | Note |
|-------|----------|------|
| "我们决定采用方案A" | ✅ present=true | Explicit decision |
| "当前任务是实现X" | ❌ present=false | No decision, just task |
| "经过权衡，选择Y因为Z" | ✅ present=true | Decision + rationale |
| "X是Y的一部分" | ❌ present=false | Just relationship |

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Coverage | >= 50% (gate-passed samples) | 0% |
| Extraction Precision | >= 80% | TBD |
| Outcome Improvement | partial → more complete | TBD |
| FP Rate Impact | <= +2% | TBD |

---

*Schema Version: 1.0*
*Created: 2026-03-09*
*Phase: D1 - Decision Context Schema Definition*
