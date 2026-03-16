# Gap Matrix: Default Autonomy Closure

**Date**: 2026-03-16
**Baseline**: Checkpointed Step Loop v2 + V3_MASTER_ACCEPTANCE_PACK

---

## Module A: 默认输入入任务链

| Capability | Current State | Gap Type | Priority |
|------------|---------------|----------|----------|
| Input parser | ❌ Not implemented | Implementation | P0 |
| Task classifier | ⚠️ Partial (autonomy_policy.py exists) | Enhancement | P1 |
| Admission gate | ⚠️ Partial (docs exist) | Contract | P0 |
| Task queue | ⚠️ Partial (pending_subtasks.json exists) | Enhancement | P1 |
| Auto-admission for low risk | ⚠️ Partial (GATE_RULES.md exists) | Contract | P0 |
| Dedup & idempotency | ⚠️ Partial (ledger.jsonl exists) | Enhancement | P1 |

**Gap Summary**:
- Contract: Need AUTO_TASK_ADMISSION_CONTRACT.md
- Implementation: Need input parser + auto-admission flow
- Tests: Need test_task_admission.py

---

## Module B: 长任务自动规划 + 重规划链

| Capability | Current State | Gap Type | Priority |
|------------|---------------|----------|----------|
| Task decomposer | ⚠️ Partial (orchestrator.py exists) | Enhancement | P0 |
| Plan generator | ⚠️ Partial (orchestrator handles plans) | Enhancement | P1 |
| Checkpoint manager | ✅ Exists (task_state.json, step_packet) | None | - |
| Replan trigger | ❌ Not implemented | Implementation | P0 |
| Progress tracker | ⚠️ Partial (task_ledger.py exists) | Enhancement | P1 |

**Gap Summary**:
- Contract: Need RESUMABLE_PLANNING_CONTRACT.md
- Implementation: Need replan trigger + progress persistence
- Tests: Need test_resumable_planning.py

---

## Module C: 执行 / 恢复 / 重试 / 回滚统一策略引擎

| Capability | Current State | Gap Type | Priority |
|------------|---------------|----------|----------|
| Execution engine | ✅ Exists (orchestrator.py) | None | - |
| Recovery handler | ⚠️ Partial (test_agent_verified_recovery.py exists) | Contract | P0 |
| Retry policy | ⚠️ Partial (failure_taxonomy.yaml exists) | Contract | P0 |
| Rollback manager | ❌ Not implemented | Implementation | P0 |
| State machine | ⚠️ Partial (task_state.json) | Enhancement | P1 |
| Compensation actions | ❌ Not implemented | Implementation | P1 |

**Gap Summary**:
- Contract: Need EXECUTION_RECOVERY_RETRY_ROLLBACK_POLICY.md
- Implementation: Need rollback manager + compensation actions
- Tests: Need test_execution_policy.py

---

## Module D: 风险门控与 blocker 升级规则

| Capability | Current State | Gap Type | Priority |
|------------|---------------|----------|----------|
| Risk classifier | ⚠️ Partial (AUTONOMY_CAPABILITY_BOUNDARY.md exists) | Contract | P0 |
| Action gate | ⚠️ Partial (forbidden_evidence.json exists) | Contract | P0 |
| Blocker detector | ⚠️ Partial (GATE_RULES.md exists) | Enhancement | P1 |
| Escalation handler | ❌ Not implemented | Implementation | P0 |
| R0-R3 classification | ❌ Not implemented | Contract | P0 |

**Gap Summary**:
- Contract: Need RISK_BLOCKER_GOVERNOR.md
- Implementation: Need R0-R3 classifier + escalation handler
- Tests: Need test_risk_governor.py

---

## Module E: 成功判定防假完成

| Capability | Current State | Gap Type | Priority |
|------------|---------------|----------|----------|
| Success criteria checker | ⚠️ Partial (GATE_RULES.md exists) | Contract | P0 |
| Evidence collector | ✅ Exists (evidence/ directory) | None | - |
| Verification gate | ⚠️ Partial (Gate A/B/C exists) | Enhancement | P1 |
| False positive detector | ❌ Not implemented | Implementation | P0 |
| Multi-layer verification | ❌ Not implemented | Implementation | P0 |

**Gap Summary**:
- Contract: Need SUCCESS_VERIFICATION_POLICY.md
- Implementation: Need false positive detector + multi-layer verification
- Tests: Need test_success_verification.py

---

## Summary: Gap Matrix

| Module | Contract Gap | Implementation Gap | Test Gap |
|--------|--------------|-------------------|----------|
| A: Task Admission | P0 | P0 | P0 |
| B: Resumable Planning | P0 | P0 | P0 |
| C: Execution Policy | P0 | P0 | P0 |
| D: Risk Governor | P0 | P0 | P0 |
| E: Success Verification | P0 | P0 | P0 |

---

## Minimum Observation Period Requirements

### Must Have Before Observation

1. **AUTO_TASK_ADMISSION_CONTRACT.md** (P0)
2. **RESUMABLE_PLANNING_CONTRACT.md** (P0)
3. **EXECUTION_RECOVERY_RETRY_ROLLBACK_POLICY.md** (P0)
4. **RISK_BLOCKER_GOVERNOR.md** (P0)
5. **SUCCESS_VERIFICATION_POLICY.md** (P0)
6. **OBSERVATION_PLAN.md** (P0)

### Can Be Enhanced During Observation

1. Implementation refinements
2. Additional tests
3. Edge case handling

---

## V2 Baseline Issue

**Critical**: `pipelines/gate-runner` missing

**Action Required**: Create or fix path before proceeding

---

## Next Steps

1. Fix v2 baseline issue
2. Create 5 contract documents (skeleton)
3. Create OBSERVATION_PLAN.md
4. Start observation period
5. Enhance implementation during observation
