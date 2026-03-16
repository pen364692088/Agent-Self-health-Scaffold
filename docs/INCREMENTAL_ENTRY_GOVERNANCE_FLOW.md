# 增量入口治理接入流程

**版本**: 1.0.0
**创建时间**: 2026-03-16
**用途**: 定义新增入口的标准治理接入流程

---

## 1. 流程概述

新增或变更入口一旦被发现，必须进入以下流程：

```
增量识别 → 边界确认 → Registry 登记 → 治理接入 → Gate 验收 → 落盘报告
```

---

## 2. 增量识别

### 2.1 触发条件

- 新增工具文件
- 新增路由
- 新增回调处理
- 新增恢复分支
- 入口文件变更

### 2.2 识别方式

```bash
# 增量扫描
python tools/policy-entry-incremental-scan --only-new

# P0/P1 检查
python tools/policy-entry-incremental-scan --only-p0-p1
```

---

## 3. 边界确认

### 3.1 分类确认

| 分类 | 条件 | 处理优先级 |
|------|------|------------|
| P0 | 影响主链执行/决策/恢复/Gate | **最高** |
| P1 | 潜在主链旁路 | **高** |
| P2 | 辅助治理/运维 | 中 |
| P3 | 测试/示例/废弃 | 低 |

### 3.2 确认问题

1. 是否真实可执行？
2. 是否影响主链？
3. 是否属于旁路/恢复/回调？
4. 是否必须纳管？

---

## 4. Registry 登记

### 4.1 必填字段

```yaml
- entry_id: "entry-XXX"
  entry_path: "tools/xxx"
  entry_type: "cli|daemon|script"
  class: "P0|P1|P2|P3"
  owner: "team-name"
  description: "入口描述"
  policy_bind_connected: true|false
  guard_connected: true|false
  hard_judge_connected: true|false
  boundary_checked: true|false
  preflight_covered: true|false
  ci_covered: true|false
  status: "active|pending_fix|deprecated"
  registered_at: "ISO8601"
```

### 4.2 登记原则

- P0/P1 必须登记
- P2 可选登记
- P3 不登记，记录在排除清单

---

## 5. 治理接入

### 5.1 接入要求

| 分类 | policy_bind | guard | hard_judge | boundary |
|------|-------------|-------|------------|----------|
| P0 | **必需** | **必需** | **必需** | **必需** |
| P1 | **必需** | **必需** | 可选 | **必需** |
| P2 | 可选 | 可选 | 不需要 | 可选 |
| P3 | 不需要 | 不需要 | 不需要 | 不需要 |

### 5.2 接入验证

```bash
# 检查治理状态
python tools/governance-hard-gate tools/xxx --json

# 检查所有注册入口
python tools/governance-hard-gate --all --json
```

---

## 6. Gate 验收

### 6.1 Gate A: 契约验证

- 入口定义完整
- 字段类型正确
- 必填字段存在

### 6.2 Gate B: E2E 验证

- 入口可执行
- 治理接入有效
- 回调/日志正常

### 6.3 Gate C: 预检验证

- 边界检查通过
- 无安全隐患
- 资源限制合理

---

## 7. 落盘报告

### 7.1 报告内容

```markdown
# 增量入口治理接入报告

## 入口信息
- entry_id: entry-XXX
- entry_path: tools/xxx
- class: P0/P1/P2

## 治理状态
- policy_bind_connected: true
- guard_connected: true
- hard_judge_connected: true/false
- boundary_checked: true

## Gate 验收
- Gate A: PASS
- Gate B: PASS
- Gate C: PASS

## 结论
✅ 入口已完整纳管
```

### 7.2 存储位置

`artifacts/governance_incremental/entry_XXX_onboarding_report.md`

---

## 8. P0/P1 优先处理

### 8.1 优先规则

- P0 入口必须在 **24 小时内** 完成纳管
- P1 入口必须在 **72 小时内** 完成纳管
- 不允许 P0/P1 长期停留在 `pending_fix`

### 8.2 阻断规则

- 未过 Gate A/B/C 不得宣称接入完成
- `status` 不得随意改为 `active`
- 治理接入缺失必须记录在案

---

## 9. 禁止行为

1. ❌ 新增入口绕过硬门禁
2. ❌ P0/P1 入口长期未纳管
3. ❌ 只登记不接入治理
4. ❌ 用 notes 掩盖缺口
5. ❌ 通过降级分类规避纳管

---

## 10. 模板

### 增量入口接入模板

```markdown
# 增量入口治理接入报告

**入口路径**: tools/xxx
**分类**: P0/P1/P2
**发现时间**: YYYY-MM-DDTHH:MM:SSZ

## 1. 边界确认

- 是否真实可执行: 是/否
- 是否影响主链: 是/否
- 是否必须纳管: 是/否

## 2. Registry 登记

- entry_id: entry-XXX
- entry_path: tools/xxx
- class: P0/P1/P2
- owner: team-name
- status: active

## 3. 治理接入

- policy_bind_connected: true/false
- guard_connected: true/false
- hard_judge_connected: true/false
- boundary_checked: true/false

## 4. Gate 验收

- Gate A: PASS/FAIL
- Gate B: PASS/FAIL
- Gate C: PASS/FAIL

## 5. 结论

✅ 入口已完整纳管 / ⚠️ 需要修复 / ❌ 排除

**处理人**: XXX
**处理时间**: YYYY-MM-DDTHH:MM:SSZ
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-16
