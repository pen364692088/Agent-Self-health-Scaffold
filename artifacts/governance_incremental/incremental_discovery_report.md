# Phase A: 增量入口发现机制报告

**执行时间**: 2026-03-16T23:00:00Z
**状态**: ✅ 完成

---

## 1. 目标

建立增量入口发现机制，让新增入口能被快速识别。

---

## 2. 实现方式

### 2.1 增量扫描工具

**工具**: `tools/policy-entry-incremental-scan`

**功能**:
- 对比当前扫描结果与基线
- 发现新增入口、变更入口、漂移入口
- 输出增量发现报告

**用法**:
```bash
# 完整增量扫描
python tools/policy-entry-incremental-scan --format json

# 仅显示新增入口
python tools/policy-entry-incremental-scan --only-new --format json

# 仅显示 P0/P1 未注册入口
python tools/policy-entry-incremental-scan --only-p0-p1 --format json

# 文本格式
python tools/policy-entry-incremental-scan --format text
```

### 2.2 发现机制

| 发现类型 | 机制 | 触发条件 |
|----------|------|----------|
| 新增入口 | 对比基线路径集合 | 当前路径不在基线中 |
| 变更入口 | 对比文件大小 | 大小变化 |
| 未注册入口 | 对比 registry | 路径不在 registry 中 |
| P0/P1 风险入口 | 关键词分类 | 疑似 P0/P1 |

### 2.3 基线管理

**基线位置**: `artifacts/governance_phase0/initial_reconcile_results.json`

**更新策略**: 每次 major release 后更新基线

---

## 3. 首次增量扫描结果

### 3.1 统计

| 指标 | 值 |
|------|-----|
| total_candidates | 235 |
| registered_entries | 21 |
| new_candidates | **1** |
| unregistered_entries | 214 |
| p0_p1_unregistered | **13** |
| drifted_entries | 0 |

### 3.2 新增入口

| 入口路径 | 分类 | 说明 |
|----------|------|------|
| tools/policy-entry-incremental-scan | P2 | 本次新增的增量扫描工具 |

### 3.3 未注册 P0/P1 入口

大部分是已排除的入口：

| 入口路径 | 状态 | 说明 |
|----------|------|------|
| tools/hook_smoke_test | 已排除 | 测试脚本 |
| tools/test-callback-* | 已排除 | 测试脚本 |
| tools/agent-recovery-summary | 已排除 | P2 重新分类 |
| tools/probe-callback-* | 已排除 | P2 重新分类 |
| tools/demo-auto-resume-restart-test | 已排除 | 演示脚本 |
| tools/session-start-recovery.bak | 已排除 | 备份文件 |
| tools/callback-daily-summary | 已排除 | P2 重新分类 |
| tools/probe-webhook-fallback | 待审查 | 新发现的 P1 |
| tools/debug-hooks | 待审查 | 新发现的 P1 |

---

## 4. 增量发现输出

每次增量扫描至少输出：

| 输出项 | 说明 |
|--------|------|
| new_candidate_entries | 新增候选入口 |
| changed_registered_entries | 变更的注册入口 |
| possible_unregistered_mainline_entries | 可能未注册的主链入口 |
| possible_registry_drift_entries | 可能的 registry 漂移 |

---

## 5. 集成建议

### 5.1 CI/CD 集成

```yaml
# .github/workflows/governance-incremental.yml
name: Governance Incremental Check
on: [push, pull_request]
jobs:
  incremental-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Incremental Scan
        run: python tools/policy-entry-incremental-scan --only-p0-p1
```

### 5.2 日常检查

```bash
# 每日增量检查
python tools/policy-entry-incremental-scan --only-p0-p1 --format json > daily_incremental.json
```

---

## 6. 交付物

| 产物 | 路径 |
|------|------|
| 增量扫描工具 | tools/policy-entry-incremental-scan |
| 增量发现报告 | artifacts/governance_incremental/incremental_discovery_report.md |
| 扫描结果 | artifacts/governance_incremental/incremental_scan_result.json |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T23:00:00Z
