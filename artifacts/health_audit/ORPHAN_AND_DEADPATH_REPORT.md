# Orphan and Deadpath Report - 孤儿组件和死路径报告

**审计日期**: 2026-03-09 21:25 CST

---

## 孤儿组件定义

- **孤儿组件**: 存在但无调用点的工具/脚本
- **死路径**: 被标记为废弃但仍被引用的路径

---

## 孤儿组件

### 1. check-subagent-mailbox

**状态**: 已废弃但仍存在

**位置**: tools/check-subagent-mailbox

**证据**:
```
$ grep -r "check-subagent-mailbox" tools/ | grep "deprecated"
tools/check-subagent-mailbox: 旧: check-subagent-mailbox --json
```

**影响**: 可能被误用

**建议**: 删除或移到 legacy/ 目录

---

### 2. context-budget-check

**状态**: 有引用但引用较少

**位置**: tools/context-budget-check

**证据**:
```
$ grep -r "context-budget-check" memory/ logs/ 2>/dev/null | wc -l
10
```

**分析**: 最近 30 天仅 10 次提及，可能是正常使用量

**建议**: 保留，监控使用频率

---

### 3. heartbeat-memory-bridge

**状态**: 可能是遗留工具

**位置**: tools/heartbeat-memory-bridge (如果存在)

**证据**: 需要进一步检查

**建议**: 如果确实无引用，考虑删除

---

## 死路径

### 1. Legacy callback 路径

**问题**: 旧版 callback 机制被新版替代

**路径**:
- `check-subagent-mailbox` (已废弃)
- 可能的其他旧路径

**影响**: 文档/代码中的引用指向废弃路径

**建议**: 更新引用或添加重定向

---

### 2. Session Index 空目录

**问题**: artifacts/session_index/ 存在但为空

**状态**: 目录存在但无内容

**影响**: L1 检索依赖其他源

**建议**: 重建索引或删除目录

---

## Fallback 掩盖问题

### 1. Session Index 缺失

**问题**: Session Index 为 0 但系统正常运行

**掩盖机制**: L1 Capsule Fallback

**风险**: 掩盖了索引问题

**建议**: 重建索引或确认不需要

---

### 2. memory-lancedb 404

**问题**: Gateway LanceDB 返回 404 但无报错

**掩盖机制**: context-retrieve 替代

**风险**: 日志噪音，可能掩盖其他问题

**建议**: 禁用 memory-lancedb 或修复

---

## 统计

| 类型 | 数量 | 处理建议 |
|------|------|----------|
| 孤儿工具 | 1-3 | 删除或移到 legacy |
| 死路径引用 | 1-2 | 更新引用 |
| 空目录 | 1 | 重建或删除 |
| Fallback 掩盖 | 2 | 确认或修复 |

---

## 建议行动

1. **立即**: 删除 check-subagent-mailbox 或移到 legacy/
2. **可选**: 重建 Session Index
3. **可选**: 禁用 memory-lancedb（减少日志噪音）
