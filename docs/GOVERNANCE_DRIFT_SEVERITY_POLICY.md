# 治理漂移严重性分级策略

**版本**: 1.0.0
**创建时间**: 2026-03-16
**用途**: 定义治理漂移的分级标准和处理规则

---

## 1. 漂移分级

### Level 0: 信息级

**定义**: 不影响主链治理的低风险漂移

**示例**:
- 新增 P2/P3 候选入口
- 辅助入口 metadata 变化
- 文档描述更新

**处理**:
- 记录在日志中
- 不需要立即处理
- 可在下次迭代中处理

---

### Level 1: 警告级

**定义**: 存在不一致但暂不影响主链安全

**示例**:
- registry 字段缺失
- owner/path 轻微不一致
- 辅助入口状态失配
- P2 入口缺少可选治理项

**处理**:
- 发送警告通知
- 进入待处理队列
- 在 7 天内修复

---

### Level 2: 高优先级

**定义**: 存在明显治理风险，需要优先处理

**示例**:
- P1 未注册新增入口
- 已纳管入口失去 bind 或 guard
- boundary 信息冲突
- 入口状态与 registry 不一致

**处理**:
- **必须入修复队列**
- 在 72 小时内修复
- 每日跟踪进度
- 无法修复时升级

---

### Level 3: 阻断级

**定义**: 严重威胁治理完整性，必须立即阻断

**示例**:
- P0 新增入口未注册
- 主链入口失去治理接入
- unresolved P0/P1 > 0
- hard gate 被绕开
- register_after_fix 重新出现

**处理**:
- **立即阻断相关接入/发布/主链推进**
- 在 24 小时内修复
- 修复后必须复验
- 记录事故报告

---

## 2. 分级判定规则

| 条件 | 级别 |
|------|------|
| 新增 P2/P3 入口 | Level 0 |
| P2 入口状态失配 | Level 1 |
| registry 字段缺失 | Level 1 |
| P1 未注册入口 | Level 2 |
| 失去 bind/guard | Level 2 |
| P0 未注册入口 | Level 3 |
| 主链治理回退 | Level 3 |
| unresolved P0/P1 > 0 | Level 3 |

---

## 3. 处理时限

| 级别 | 处理时限 | 升级条件 |
|------|----------|----------|
| Level 0 | 无限期 | 无 |
| Level 1 | 7 天 | 超时升级为 Level 2 |
| Level 2 | 72 小时 | 超时升级为 Level 3 |
| Level 3 | 24 小时 | 超时触发事故流程 |

---

## 4. 阻断规则

### 4.1 Level 3 阻断

当出现 Level 3 漂移时，必须：

1. **立即阻断** 相关入口的主链访问
2. **暂停** 相关入口的发布/部署
3. **通知** 治理负责人
4. **启动** 紧急修复流程

### 4.2 阻断解除条件

- 入口已完整纳管
- Gate A/B/C 全部通过
- 治理状态恢复正常
- 事故报告已完成

---

## 5. 通知机制

| 级别 | 通知方式 | 接收人 |
|------|----------|--------|
| Level 0 | 日志记录 | 无 |
| Level 1 | 邮件/消息 | 入口 owner |
| Level 2 | 邮件 + 消息 + 日志 | owner + 治理团队 |
| Level 3 | 全渠道通知 + 阻断警报 | owner + 治理团队 + 值班 |

---

## 6. 漂移检测

### 6.1 检测方式

```bash
# 增量扫描
python tools/policy-entry-incremental-scan --only-p0-p1

# hard-gate 检查
python tools/governance-hard-gate --all

# reconcile 检查
python tools/policy-entry-reconcile --format json
```

### 6.2 检测频率

| 检测项 | 频率 |
|--------|------|
| P0/P1 状态 | 每日 |
| 全量入口扫描 | 每周 |
| 增量入口检查 | 每次 CI/CD |
| registry 一致性 | 每次变更 |

---

## 7. 漂移报告

每次检测输出：

```json
{
  "scan_timestamp": "ISO8601",
  "drift_level": "Level 0/1/2/3",
  "drift_items": [
    {
      "entry_path": "tools/xxx",
      "drift_type": "missing_bind|missing_guard|...",
      "severity": "Level X",
      "recommended_action": "..."
    }
  ],
  "statistics": {
    "total_drifts": 0,
    "by_level": {
      "level_0": 0,
      "level_1": 0,
      "level_2": 0,
      "level_3": 0
    }
  }
}
```

---

## 8. 事故流程

### 8.1 Level 3 事故

当出现 Level 3 漂移时：

1. **发现**: 自动检测或人工发现
2. **阻断**: 立即阻断相关入口
3. **通知**: 通知所有相关人员
4. **修复**: 在 24 小时内修复
5. **复验**: 修复后必须通过 Gate A/B/C
6. **报告**: 输出事故报告

### 8.2 事故报告模板

```markdown
# 治理漂移事故报告

**时间**: YYYY-MM-DDTHH:MM:SSZ
**级别**: Level 3
**入口**: tools/xxx

## 问题
- 问题描述
- 影响范围

## 处理
- 处理措施
- 修复时间

## 验证
- Gate A: PASS
- Gate B: PASS
- Gate C: PASS

## 结论
✅ 问题已解决

**处理人**: XXX
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-16
