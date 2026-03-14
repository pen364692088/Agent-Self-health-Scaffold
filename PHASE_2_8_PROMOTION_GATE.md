# Phase 2.8: Promotion Readiness Gate

## Objective
用真实任务样本评估 shadow prompt / shadow recovery 相对当前主链的表现，输出分级决策。

## Constraints
- ❌ 不引入 handoff/capsule 作为主输入
- ❌ 不替代当前主链
- ❌ 不新增第二套 live state
- ✅ 决策必须基于真实样本评估

## Evaluation Dimensions

### 1. Prompt Readiness
| Metric | Target | Weight |
|--------|--------|--------|
| Canonical Coverage | ≥ 90% | 30% |
| Bridge Fallback Rate | ≤ 5% | 20% |
| Conflict Rate | ≤ 3% | 15% |
| Missing Field Rate | ≤ 2% | 15% |
| Prompt Token Efficiency | ≤ 1.2x baseline | 20% |

### 2. Recovery Readiness
| Metric | Target | Weight |
|--------|--------|--------|
| Recovery Match Rate | ≥ 85% | 35% |
| Phase Match Rate | ≥ 90% | 25% |
| Next Step Match Rate | ≥ 80% | 20% |
| Blocker Visibility | ≥ 95% | 20% |

### 3. Grade Levels
| Grade | Score | Decision |
|-------|-------|----------|
| A | ≥ 90 | Prompt Limited Pilot |
| B | 75-89 | Continue Shadow + Patch Gaps |
| C | 60-74 | Major Gaps + Re-evaluate |
| D | < 60 | Escalate to Phase 3 Kernel |

## Sample Sources
- session_continuity_events.jsonl (5606 events)
- Recovery success events (387)
- Task close events (17)
- Gate completed events (17)
- Conflict resolution events (5)

## Evaluation Process
1. Extract sample sessions from events
2. Run shadow prompt assembly for each sample
3. Compare with baseline prompt
4. Run shadow recovery preview for each sample
5. Compare with actual recovery outcome
6. Calculate metrics
7. Output grade and decision
