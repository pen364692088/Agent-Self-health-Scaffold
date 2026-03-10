# Wiring Map - 主链接线图

**审计日期**: 2026-03-09 21:25 CST

---

## 核心流程接线

### 1. Session Start Flow

```
新 Session 启动
    │
    ├─→ AGENTS.md 规定必须调用
    │       │
    │       └─→ session-start-recovery --recover --summary
    │               │
    │               ├─→ 读取 SESSION-STATE.md
    │               ├─→ 读取 working-buffer.md
    │               ├─→ 读取 handoff.md
    │               ├─→ 读取 WAL
    │               └─→ 调用 retrieve_memory_constraints()
    │                       │
    │                       └─→ 直接读取 artifacts/capsules/*.json
    │                               │
    │                               └─→ 返回 hard_constraints
    │
    └─→ 输出恢复摘要 → 影响后续行为
```

**接线状态**: ✅ 完整

---

### 2. Heartbeat Flow

```
Heartbeat 触发
    │
    ├─→ HEARTBEAT.md 定义检查流程
    │       │
    │       ├─→ Session Recovery Check
    │       │       └─→ session-start-recovery --recover --json
    │       │
    │       ├─→ State Flush Check
    │       │       └─→ 检查 context ratio
    │       │
    │       ├─→ Self-Health Quick Mode
    │       │       └─→ agent-self-health-scheduler --mode quick
    │       │
    │       ├─→ Route Rebind Guard Check
    │       │       └─→ route-rebind-guard-heartbeat --json
    │       │
    │       └─→ Shadow Mode Check (Conditional)
    │               └─→ shadow_watcher --run-once --quiet
    │
    └─→ 输出 HEARTBEAT_OK 或 ALERT
```

**接线状态**: ✅ 完整（Shadow Mode 除外）

**缺失**: probe-execution-policy-v2 未接入

---

### 3. 子代理完成 Flow

```
子代理完成
    │
    └─→ 写 receipt 到 reports/subtasks/
            │
            └─→ callback-worker.path 监听
                    │
                    └─→ 触发 callback-worker.service
                            │
                            └─→ 调用 openclaw message send
                                    │
                                    └─→ 发送通知到用户
```

**接线状态**: ✅ 完整

---

### 4. 记忆检索 Flow

```
记忆检索请求
    │
    └─→ context-retrieve --query "..."
            │
            ├─→ L1: Capsule Fallback
            │       ├─→ 读取 artifacts/capsules/*.json
            │       └─→ 关键词匹配
            │
            ├─→ L1: Session Index
            │       ├─→ 读取 artifacts/session_index/*.json
            │       └─→ (当前为 0 个文件)
            │
            └─→ L2: OpenViking
                    ├─→ openviking health
                    ├─→ openviking find
                    └─→ 返回语义匹配结果
```

**接线状态**: ⚠️ 部分受损
- L1 Capsule: ✅ 工作
- L1 Session Index: ❌ 无文件
- L2 OpenViking: ⚠️ embedding 错误但可用

---

### 5. Execution Policy Flow

```
敏感路径操作
    │
    ├─→ 请求使用 edit/write 工具
    │       │
    │       └─→ policy-eval --path --tool
    │               │
    │               └─→ 返回 ALLOW/DENY/WARN
    │
    ├─→ 如果 DENY
    │       └─→ 使用 safe-write/safe-replace 替代
    │
    └─→ 任务完成
            └─→ verify-and-close --task-id
```

**接线状态**: ⚠️ 部分接线
- policy-eval: ✅ 工作
- safe-write/safe-replace: ✅ 工作
- verify-and-close: ⚠️ 未被广泛使用
- Heartbeat 集成: ❌ 未接线

---

## 入口点总结

| 入口 | 接入模块 | 状态 |
|------|----------|------|
| AGENTS.md | session-start-recovery | ✅ |
| HEARTBEAT.md | 多个检查项 | ⚠️ 缺 Execution Policy |
| TOOLS.md | subtask-orchestrate | ✅ |
| SOUL.md | Task Completion Protocol | ⚠️ 未强制执行 |
| callback-worker.path | 子代理完成通知 | ✅ |

---

## 未接线模块

| 模块 | 原因 | 风险 |
|------|------|------|
| probe-execution-policy-v2 | HEARTBEAT.md 未引用 | 中 |
| shadow_watcher | 环境变量未设置 | 低 |
| verify-and-close | 无强制调用点 | 中 |
| session-indexer | 无触发机制 | 低 |
