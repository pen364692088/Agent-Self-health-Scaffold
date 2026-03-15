# Self-Healing System Evidence Report

生成日期: 2026-03-15

---

## 状态说明

⚠️ **当前状态**: 实现完成，证据收集中

| 阶段 | 实现状态 | 证据状态 |
|-----|---------|---------|
| P0 | ✅ 完成 | 🟡 收集中 |
| P1 | ✅ 完成 | 🟡 收集中 |
| P2 | ✅ 完成 | 🟡 收集中 |

---

## 已收集证据

### 证据 1: edit failed → 自愈修复闭环

**测试文件**: `tests/test_self_healing_e2e.py`

**已验证**:
- ✅ Failure Orchestrator 接管失败事件
- ✅ Bundle 生成成功 (bundle_id, signature)
- ✅ L1/L2 诊断签名生成
- ✅ 3+ 候选修复方案生成
- 🔄 沙箱验证 (git worktree 问题已修复，待重跑)

**待完成**:
- Gate A/B/C 实跑输出
- Patch 生成验证

---

### 证据 2: 同类问题二次命中历史经验

**状态**: 🔄 待完成

**依赖**: 需要先成功运行证据1两次，建立历史记忆

---

### 证据 3: preflight 拦截高危 edit

**测试结果**: ✅ 通过

```
[1] 尝试 edit 高危文件: SOUL.md
    ✅ Preflight 拦截成功!
    🛡️  匹配规则: 保护核心身份文件
    🚫 自动级别: L0
```

**证据文件**: `artifacts/self_healing/e2e_test_results.json`

---

### 证据 4: Gate A/B/C 实跑输出

**状态**: 🔄 待完成

需要修复 sandbox healer 后重新运行测试获取完整 Gate 输出。

---

### 证据 5: shadow learning 样例

**实现状态**: ✅ 代码已完成

**文件**: `src/self_healing/shadow_planner/collector.py`

**功能**:
- 外部模式采集
- 蒸馏成模板
- 影子验证流程
- 晋升机制

**待完成**: 实际采集一个外部模式并走完流程

---

### 证据 6: 7-14 天观察窗口指标报告

**状态**: 🔄 待完成

需要运行系统7-14天收集真实指标数据。

---

## 已提交代码

| Commit | 内容 |
|--------|------|
| 78ac2f0 | Phase 0-4 首期闭环 |
| 29c0022 | Phase 5-7 二期、三期闭环 |
| 8f5444e | 修复 sandbox healer + E2E 测试框架 |

---

## 下一步

1. 重新运行 E2E 测试获取完整证据
2. 运行两次建立历史记忆
3. 采集一个外部模式走完 shadow learning 流程
4. 部署系统运行7-14天收集指标

---

*报告生成时间: 2026-03-15 01:25 CDT*
