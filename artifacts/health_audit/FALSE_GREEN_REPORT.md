# False Green Report - 表面健康但实际无效的模块报告

**审计日期**: 2026-03-09 21:25 CST

---

## 定义

**False Green**: 模块显示健康状态（✅）但实际未产生预期效果

---

## 1. Execution Policy 样本

### 表面状态
```
$ tools/policy-daily-check
=== Policy Daily Check (2026-03-09) ===
...
❌ 样本尚未开始积累
```

### 分析

- **工具状态**: ✅ 所有工具存在且工作
- **配置状态**: ✅ 规则已定义
- **运行状态**: ❌ 无样本积累
- **原因**: 真实任务未触发敏感路径操作

### 是否 False Green?

**是**: 系统显示健康（工具工作）但无实际拦截效果

**根因**: 缺少真实使用场景触发

**建议**: 
1. 人工触发测试场景
2. 或接受当前状态（等待自然触发）

---

## 2. Shadow Mode

### 表面状态
```
$ ls artifacts/context_compression/shadow_config.json
存在
```

### 分析

- **配置状态**: ✅ 配置文件存在
- **声明状态**: ✅ HEARTBEAT.md 声明
- **运行状态**: ❌ 环境变量未设置
- **实际效果**: 无

### 是否 False Green?

**是**: 配置存在但未启用

**根因**: AUTO_COMPACTION_SHADOW_MODE 环境变量缺失

**建议**: 设置环境变量或删除配置

---

## 3. Session Index

### 表面状态
```
$ tools/context-retrieve --health
L1 (Capsule Fallback): ✅
L1 (Session Index): (未显示)
```

### 分析

- **目录状态**: ✅ 目录存在
- **内容状态**: ❌ 0 个文件
- **系统状态**: ✅ 正常运行（Capsule 兜底）
- **实际效果**: L1 部分功能缺失

### 是否 False Green?

**部分**: 系统正常但功能不完整

**根因**: Session Index 未生成

**建议**: 重建索引

---

## 4. verify-and-close

### 表面状态
```
$ ls tools/verify-and-close
存在
```

### 分析

- **工具状态**: ✅ 存在
- **文档状态**: ✅ SOUL.md 规定必须使用
- **实际调用**: ❌ 无 receipt 生成
- **实际效果**: 任务可能绕过验证

### 是否 False Green?

**是**: 工具存在但未被强制使用

**根因**: 缺少强制调用机制

**建议**: 在输出层添加检查

---

## 5. memory-lancedb

### 表面状态
```
$ systemctl --user is-active openclaw-gateway.service
active
```

### 分析

- **服务状态**: ✅ Gateway 运行中
- **日志状态**: ⚠️ 频繁 404 错误
- **实际效果**: LanceDB 功能不可用
- **替代方案**: context-retrieve 工作正常

### 是否 False Green?

**是**: Gateway 显示健康但内置功能受损

**根因**: LanceDB 服务未配置

**建议**: 禁用或修复

---

## 总结

| 模块 | 表面状态 | 实际状态 | False Green | 原因 |
|------|----------|----------|-------------|------|
| Execution Policy 样本 | ✅ 工具工作 | ❌ 无样本 | ✅ 是 | 缺少触发场景 |
| Shadow Mode | ✅ 配置存在 | ❌ 未启用 | ✅ 是 | 环境变量缺失 |
| Session Index | ✅ 目录存在 | ❌ 无内容 | ⚠️ 部分 | 索引未生成 |
| verify-and-close | ✅ 工具存在 | ❌ 未强制 | ✅ 是 | 无强制机制 |
| memory-lancedb | ✅ Gateway 活跃 | ❌ 404 错误 | ✅ 是 | 服务未配置 |

---

## 修复优先级

| 优先级 | 模块 | 修复难度 | 建议 |
|--------|------|----------|------|
| P1 | verify-and-close | 中 | 添加强制检查 |
| P1 | Execution Policy | 低 | 等待自然触发 |
| P2 | Shadow Mode | 低 | 设置环境变量 |
| P2 | Session Index | 中 | 重建索引 |
| P2 | memory-lancedb | 低 | 忽略或禁用 |
