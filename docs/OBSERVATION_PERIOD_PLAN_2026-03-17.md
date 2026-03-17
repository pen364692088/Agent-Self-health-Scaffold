# Self-Health v2 观察期执行方案

**生效时间**: 2026-03-17T21:48:00Z
**基线 Tag**: `self-health-v2-obs-day0`
**观察周期**: 7 天（可提前毕业或延长）

---

## 一、观察期目标

验证"最小闭环达成"在真实生产环境中的稳定性，收集足够样本以判定：
- **Promote**: 正式毕业，进入稳定运维期
- **Extend**: 延长观察期，收集更多样本
- **Rollback**: 回滚修复，重新进入开发期

---

## 二、观察维度与指标

### 核心指标

| 指标 | 定义 | 目标 |
|------|------|------|
| 自动恢复成功率 | 成功恢复次数 / 总恢复机会次数 | ≥ 95% |
| 人工补继续次数 | 用户手动发送"继续"类命令的次数 | = 0 |
| 恢复耗时 P95 | 从 gateway restart 到 auto-resume 完成的耗时 | ≤ 5s |
| 误恢复率 | 不应恢复但被恢复的次数 / 总恢复次数 | = 0% |
| 漏恢复率 | 应恢复但未恢复的次数 / 总恢复机会次数 | ≤ 5% |

### 辅助指标

| 指标 | 定义 | 监控方式 |
|------|------|----------|
| Gate A/B/C 通过率 | 每日定时检查结果 | systemd timer |
| auto-resume 触发次数 | gateway restart 后的触发记录 | journalctl |
| 恢复后任务完成率 | 恢复后的任务最终完成比例 | run-state |
| 恢复风暴检测 | 短时间内多次重复恢复同一任务 | 自定义脚本 |

---

## 三、样本计数规则

### 什么算一次"恢复机会"

满足以下条件之一：
1. `gateway restart` 发生时，`run-state.status = running`
2. `gateway restart` 发生时，`orchestrator.pending_count > 0`
3. `gateway restart` 发生时，`workflow.running_steps` 非空

### 什么算"成功恢复"

满足以下全部条件：
1. `auto-resume-orchestrator.service` 被触发
2. `"action": "resumed"` 或 `"action": "wait"`（任务继续推进）
3. 无人工发送"继续"类命令
4. 恢复后任务状态正确推进

### 什么算"失败恢复"

满足以下任一条件：
1. `auto-resume-orchestrator.service` 未触发但应触发
2. 触发后任务状态未推进
3. 需要人工发送"继续"才能推进
4. 恢复后任务重复执行已完成步骤

### 什么算"误恢复"

满足以下任一条件：
1. 已完成任务被重复执行
2. 已失败任务被错误恢复
3. 恢复后产生数据不一致

---

## 四、每日检查流程

### 自动检查（每 5 分钟）

```
systemd timer: agent-self-health-gate.timer
  → gate-self-health-check --write --json
  → 写入 artifacts/self_health/gate_reports/
```

### 每日汇总（每天 00:00）

1. **收集指标**
   ```bash
   # 统计过去 24 小时的恢复事件
   journalctl --user -u auto-resume-orchestrator.service --since "1 day ago" \
     | grep -c '"action": "resumed"'
   
   # 统计 gateway restart 次数
   journalctl --user -u openclaw-gateway.service --since "1 day ago" \
     | grep -c "Started openclaw-gateway.service"
   ```

2. **检查四条红线**
   - ❌ 红线 1: 有人工补"继续"
   - ❌ 红线 2: 有重复执行已完成的步骤
   - ❌ 红线 3: 有 ledger 分叉
   - ❌ 红线 4: 有恢复后停滞超过 5 分钟

3. **记录样本**
   - 写入 `artifacts/self_health/observation/daily_report_YYYYMMDD.json`

---

## 五、成功率门槛

### 毕业门槛（Promote）

| 条件 | 门槛 |
|------|------|
| 观察天数 | ≥ 7 天 |
| 样本总数 | ≥ 10 次（恢复机会） |
| 自动恢复成功率 | ≥ 95% |
| 人工补继续次数 | = 0 |
| 误恢复次数 | = 0 |
| 红线违规次数 | = 0 |

### 延长门槛（Extend）

| 条件 | 说明 |
|------|------|
| 样本不足 | 样本总数 < 10 次，但无红线违规 |
| 边缘案例 | 有 1-2 次失败需分析根因 |

### 回滚门槛（Rollback）

| 条件 | 触发值 |
|------|--------|
| 人工补继续次数 | ≥ 1 次 |
| 自动恢复成功率 | < 80% |
| 误恢复次数 | ≥ 1 次 |
| 红线违规次数 | ≥ 1 次 |

---

## 六、毕业标准（Promote Criteria）

全部满足以下条件：

1. **样本充足**: 恢复机会次数 ≥ 10
2. **成功率达标**: 自动恢复成功率 ≥ 95%
3. **零人工干预**: 人工补继续次数 = 0
4. **零误恢复**: 误恢复次数 = 0
5. **零红线**: 四条红线全部未触发

**毕业后动作**:
- 更新 `SESSION-STATE.md` 状态为 `stable`
- 创建 tag `self-health-v2-stable`
- 关闭观察期监控，转为日常运维

---

## 七、回滚触发条件（Rollback Criteria）

满足以下任一条件立即回滚：

| 红线 | 触发条件 | 严重性 |
|------|----------|--------|
| R1: 人工补继续 | ≥ 1 次 | Critical |
| R2: 重复执行 | ≥ 1 次 | Critical |
| R3: Ledger 分叉 | ≥ 1 次 | Critical |
| R4: 恢复后停滞 | ≥ 1 次（超过 5 分钟） | High |
| 成功率跌落 | < 80% | High |
| 误恢复 | ≥ 1 次 | Critical |

**回滚后动作**:
1. 立即停止观察期
2. 分析根因
3. 回退到"构件层"状态
4. 修复后重新启动观察期

---

## 八、观察期日志结构

### 每日报告

```json
{
  "date": "2026-03-18",
  "day_number": 1,
  "gate_status": {
    "A": "PASS",
    "B": "PARTIAL",
    "C": "PASS"
  },
  "recovery_opportunities": 2,
  "successful_recoveries": 2,
  "failed_recoveries": 0,
  "manual_continues": 0,
  "false_recoveries": 0,
  "red_lines": {
    "manual_continue": false,
    "duplicate_execution": false,
    "ledger_fork": false,
    "stalled_after_recovery": false
  },
  "recovery_times_seconds": [1.2, 0.8],
  "notes": "正常"
}
```

### 汇总报告

```json
{
  "observation_period": "2026-03-17 to 2026-03-24",
  "total_days": 7,
  "total_recovery_opportunities": 15,
  "total_successful_recoveries": 15,
  "success_rate": 1.0,
  "manual_continues": 0,
  "false_recoveries": 0,
  "red_line_violations": 0,
  "decision": "Promote",
  "evidence_path": "artifacts/self_health/observation/summary_20260324.json"
}
```

---

## 九、执行工具

### 创建观察期目录

```bash
mkdir -p artifacts/self_health/observation
```

### 每日报告生成脚本

```bash
~/.openclaw/workspace/tools/self-health-observation-report --date 2026-03-18
```

### 汇总报告生成脚本

```bash
~/.openclaw/workspace/tools/self-health-observation-summary --end-date 2026-03-24
```

---

## 十、当前状态

| 项目 | 值 |
|------|-----|
| 观察期开始 | 2026-03-17T21:48:00Z |
| 预计结束 | 2026-03-24T21:48:00Z |
| 当前样本数 | 11 次（历史） |
| 当前成功率 | 100% |
| 红线违规 | 0 |
| 当前判定 | 进行中 |

---

## 十一、下一步

1. 创建 `artifacts/self_health/observation/` 目录
2. 创建每日报告生成脚本
3. 等待自然发生的 gateway restart 或触发测试场景
4. Day 7 生成汇总报告并判定
