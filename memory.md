# Memory Bootstrap (Minimal)

**Purpose**: session bootstrap cheat sheet only. Full history lives in indexed memory/OpenViking.

## Core tools
```bash
# Preferred subagent orchestration
~/.openclaw/workspace/tools/subtask-orchestrate run "<task>" -m baiduqianfancodingplan/qianfan-code-latest
~/.openclaw/workspace/tools/subtask-orchestrate status
~/.openclaw/workspace/tools/subtask-orchestrate resume

# Memory retrieval
~/.openclaw/workspace/tools/session-query "<query>"
openviking find "<query>" -u viking://resources/user/memory/
```

## Hard rules
- 子代理正式主链路：`subtask-orchestrate` + `subagent-inbox`
- 不把 `sessions_send` 当关键完成回执主链路
- 先检索最小范围，再读取最小片段
- 不在 bootstrap 文件里堆历史细节
- 归档 = 每日日志 + bootstrap 摘要 + 索引/向量归档 + 顶层备份提交

## Retrieval triggers
以下情况先检索：
- 历史决策
- 参数/阈值
- 配置位置
- 旧故障模式
- 协议细节

推荐顺序：
1. `session-query`
2. 必要时 `openviking find`

## User/project reminders
- 稳定优先于花哨
- 重要里程碑要能回溯证据
- 数据/工具类任务优先走确定性流程

## Maintenance rule
如果新增内容：
- 规则/入口：这里只留简版
- 历史/细节：写到 archive、docs、POLICIES 或 OpenViking
- 目标：保持这个文件短小、可快速注入

---

## 2026-03-06: Context Compression Pipeline v1.0

### 核心架构

**三层上下文模型**：
- Resident Layer: 常驻（任务目标、open_loops、硬约束）
- Active Layer: 活动（最近 6-12 轮对话）
- Recall Layer: 回填（capsule + vector 检索）

**两级检索**：
- L1: Capsule Fallback (always available, confidence 0.85)
- L2: Vector Enhancement (optional, confidence 0.65)

### 工具位置

```bash
tools/context-budget-check    # Token 压力估算
tools/capsule-builder         # 结构化胶囊提取
tools/context-compress        # 压缩执行器 (Shadow/Enforced)
tools/context-retrieve        # 两级检索
tools/prompt-assemble         # Prompt 组装器
tools/s1-dashboard            # S1 监控面板
tools/gate1-check             # Gate 1 判定脚本
```

### Schemas

```bash
schemas/active_state.v1.schema.json
schemas/session_capsule.v1.schema.json
schemas/compression_event.v1.schema.json
schemas/budget_snapshot.v1.schema.json
```

### Policies

```bash
POLICIES/CONTEXT_COMPRESSION.md          # 核心原则
POLICIES/CONTEXT_COMPRESSION_ROLLOUT.md  # Gate 系统 + 分阶段 rollout
POLICIES/S1_FEATURE_FREEZE.md            # S1 功能冻结规则
POLICIES/S1_SAMPLE_COUNTING_RULES.md     # 样本计数 + blocker 白名单
```

### Gate 系统

```
Gate 0: Minimal Closure (L1 可用)
Gate 1: Capsule Shadow Ready (S1 指标达标)
Gate 2: Full Retrieval Ready (L2 健康 + S2 达标)
```

### 当前状态

```
阶段: S1 Shadow Validation (Feature Frozen)
启用: ❌ 未接入主链路
Gate 0: ✅ PASSED
Gate 1: ⏳ PENDING (样本 12/80)
```

### 已知问题

- Issue #1: context-retrieve L2 参数错误 (非 blocker, Gate 2 准备项)

### 集成时机

Gate 1 通过后，再考虑 session 编排层接入。
当前只作为独立工具，不改变 active session 行为。

---

Added: 2026-03-06 12:13 CST
