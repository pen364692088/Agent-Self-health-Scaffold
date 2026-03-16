# 治理漂移严重性报告

**执行时间**: 2026-03-16T23:20:00Z
**状态**: ✅ 完成

---

## 1. 漂移扫描结果

### 1.1 总体统计

| 级别 | 数量 | 说明 |
|------|------|------|
| Level 0 | 1 | 新增 P2 入口 |
| Level 1 | 1 | registry 不一致 |
| Level 2 | 7 | 缺少治理接入 |
| Level 3 | 0 | **无阻断级漂移** ✅ |
| **总计** | **9** | |

---

## 2. Level 0: 信息级

### 2.1 新增 P2 入口

| 入口路径 | 分类 | 说明 |
|----------|------|------|
| tools/policy-entry-incremental-scan | P2 | 本次新增的增量扫描工具 |

**处理**: 记录，无需立即处理

---

## 3. Level 1: 警告级

### 3.1 Registry 不一致

| entry_id | 入口路径 | 问题 |
|----------|----------|------|
| entry-015 | tools/resume_readiness_calibration.py | not_executable |

**处理**: 可接受，Python 脚本不需要执行权限

---

## 4. Level 2: 高优先级

### 4.1 缺少 hard_judge 的 P0 入口

| 入口路径 | 分类 | 缺失项 |
|----------|------|--------|
| tools/subtask-orchestrate | P0 | hard_judge |
| tools/callback-worker | P0 | hard_judge |
| tools/auto-resume-orchestrator | P0 | guard, boundary, hard_judge |
| tools/session-recovery-check | P0 | hard_judge |
| tools/agent-recovery-verify | P0 | hard_judge |
| tools/resume_readiness_calibration.py | P0 | guard, boundary, hard_judge |
| tools/resume_readiness_evaluator_v2.py | P0 | guard, boundary, hard_judge |

**处理**: 
- 已记录在例外注册表
- 限期 7 天内补齐
- 每日跟踪进度

---

## 5. Level 3: 阻断级

**无 Level 3 漂移** ✅

---

## 6. 漂移趋势

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| unresolved P0 | 0 | 0 | ✅ 达标 |
| unresolved P1 | 0 | 0 | ✅ 达标 |
| register_after_fix | 0 | 0 | ✅ 达标 |
| Level 3 漂移 | 0 | 0 | ✅ 达标 |
| Level 2 漂移 | 7 | 0 | ⚠️ 待处理 |

---

## 7. 下一步行动

### 7.1 立即处理

- 无 Level 3 漂移，无需立即处理

### 7.2 7 天内处理

- 补齐 7 个 P0 入口的治理接入
- 更新例外注册表到期时间

### 7.3 持续监控

- 每日运行增量扫描
- 每周检查例外状态

---

## 8. 交付物

| 产物 | 路径 |
|------|------|
| 漂移严重性报告 | artifacts/governance_incremental/drift_severity_report.md |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T23:20:00Z
