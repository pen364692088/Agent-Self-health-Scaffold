# Minimal Fix Plan - 最小修复计划

**审计日期**: 2026-03-09 21:25 CST

---

## 修复原则

1. 优先修主链，不优先修外围保险链
2. 优先删重复、删假启用、删无效路径
3. 优先找"真实问题是否被解决"
4. 不要把 shadow/fallback 正常运行误判为主链健康

---

## P1 修复项 (必须执行)

### 1. Execution Policy 集成到 Heartbeat

**问题**: probe-execution-policy-v2 未接入 Heartbeat

**修复方案**:
在 HEARTBEAT.md 的 Self-Health Quick Mode Hook 之后添加：

```markdown
## Execution Policy Quick Check (每次 heartbeat) ⭐⭐⭐

**每次 heartbeat 静默执行**：

```bash
~/.openclaw/workspace/tools/probe-execution-policy-v2 --quick --json >/dev/null 2>&1 || true
```

**行为**：
- 静默检查最近违规
- 记录到审计日志
- 不改变 heartbeat 输出契约
```

**执行命令**:
```bash
# 使用 safe-replace 添加到 HEARTBEAT.md
```

**风险**: 低
**预计时间**: 5 分钟

---

### 2. verify-and-close 强制执行机制

**问题**: 任务完成可能绕过验证

**修复方案**:
创建 tools/output-interceptor，在 message tool 调用前检查 receipt

**执行命令**:
```bash
# 方案 A: 创建 output-interceptor
# 方案 B: 在 safe-message 中添加检查
```

**风险**: 中
**预计时间**: 30 分钟

**当前状态**: safe-message 已存在，需增强检查

---

## P2 修复项 (技术债，可选执行)

### 3. 启用 Shadow Mode

**问题**: 环境变量未设置

**修复方案**:
```bash
# 方案 A: 设置环境变量
export AUTO_COMPACTION_SHADOW_MODE=true

# 方案 B: 删除相关配置
rm artifacts/context_compression/shadow_config.json
```

**风险**: 低
**预计时间**: 1 分钟

---

### 4. 重建 Session Index

**问题**: Session Index 为空

**修复方案**:
```bash
# 运行 session-indexer
tools/session-indexer --rebuild
```

**风险**: 低
**预计时间**: 5 分钟

---

### 5. 删除孤儿组件

**问题**: check-subagent-mailbox 已废弃

**修复方案**:
```bash
# 移到 legacy 目录
mkdir -p tools/legacy
mv tools/check-subagent-mailbox tools/legacy/
```

**风险**: 低
**预计时间**: 1 分钟

---

### 6. 禁用 memory-lancedb

**问题**: Gateway LanceDB 404 错误

**修复方案**:
```bash
# 方案 A: 在 Gateway 配置中禁用
# 方案 B: 忽略（当前状态）
```

**风险**: 低
**预计时间**: 5 分钟

---

## 执行顺序

| 顺序 | 修复项 | 优先级 | 预计时间 |
|------|--------|--------|----------|
| 1 | Execution Policy 集成 | P1 | 5 分钟 |
| 2 | verify-and-close 强制执行 | P1 | 30 分钟 |
| 3 | 删除孤儿组件 | P2 | 1 分钟 |
| 4 | 启用/删除 Shadow Mode | P2 | 1 分钟 |
| 5 | 重建 Session Index | P2 | 5 分钟 |
| 6 | 禁用 memory-lancedb | P2 | 5 分钟 |

**总计**: 约 47 分钟

---

## 验收标准

| 修复项 | 验收标准 |
|--------|----------|
| Execution Policy 集成 | HEARTBEAT.md 包含 probe-execution-policy-v2 |
| verify-and-close 强制执行 | 任务完成时生成 receipt |
| 删除孤儿组件 | tools/ 无 check-subagent-mailbox |
| Shadow Mode | 环境变量设置或配置删除 |
| Session Index | artifacts/session_index/ 有文件 |
| memory-lancedb | 无 404 日志或 Gateway 配置更新 |
