# SYSTEM_RESPONSIBILITY_BOUNDARY.md

**版本**: v1.0  
**日期**: 2026-03-17  
**状态**: 正式边界文档

---

## 0. 核心定位

`Agent-Self-health-Scaffold` 是：

> **面向所有 Agent 的统一运行保障底座（Runtime Reliability Layer），负责持久化记忆、长期指令遵循、可靠任务执行、运行健康监控与异常恢复。**

它是一个 **runtime/platform 层**，不是业务功能层。

---

## 1. 系统职责边界

### Scaffold 必须负责的内容

| 能力域 | 具体职责 |
|--------|----------|
| **Memory Runtime** | 长期记忆持久化、新会话/重启后记忆恢复、handoff 状态恢复、execution state 恢复、instruction rules 读取与解释、记忆写回、记忆证据链 |
| **Execution Runtime** | task runtime、runtime preflight、mutation guard、canonical repo/path/state guard、checkpoint/retry/recovery、artifact/receipt/audit |
| **Health Runtime** | session health、task health、memory health、repo/workspace health、drift detection、block/warning/recovery、self-healing hooks |

### Scaffold 不负责的内容

| 内容 | 归属系统 |
|------|----------|
| 情感机制、自我模型、反思/叙事/认知策略、主体意识相关逻辑 | **OpenEmotion** |
| 用户交互、Telegram/UI/消息入口、产品层路由、壳层业务流程 | **EgoCore** |
| 特定 Agent 的工作流知识、项目私有业务逻辑、独有长期业务判断 | **Agent 私有记忆空间** |

---

## 2. 与其他系统的关系

```
┌─────────────────────────────────────────────────────────┐
│                    EgoCore (产品壳层)                    │
│         用户交互 · 消息入口 · 产品路由 · UI              │
└─────────────────────────┬───────────────────────────────┘
                          │ 调用
┌─────────────────────────▼───────────────────────────────┐
│               Agent-Self-health-Scaffold                │
│              (Runtime Reliability Layer)                │
├─────────────────┬─────────────────┬─────────────────────┤
│ memory_runtime  │execution_runtime│   health_runtime    │
│  记忆持久化      │   可靠执行       │    健康监控         │
│  记忆恢复       │   preflight      │    异常检测         │
│  指令遵循       │   guard          │    自愈触发         │
└────────┬────────┴────────┬────────┴──────────┬──────────┘
         │                 │                   │
         └─────────────────┼───────────────────┘
                           │ 接入
         ┌─────────────────▼─────────────────┐
         │           OpenEmotion              │
         │       (主体认知/情感内核)            │
         │    情感 · 自我模型 · 反思 · 叙事     │
         └────────────────────────────────────┘
```

### 职责说明

| 系统 | 职责 | 边界 |
|------|------|------|
| **Scaffold** | 运行保障底座 | 提供能力，不承包业务内容 |
| **EgoCore** | 产品壳层 | 用户交互，调用 Scaffold 能力 |
| **OpenEmotion** | 主体内核 | 认知/情感/自我模型，依赖 Scaffold 持久化 |

---

## 3. 核心边界原则

### 原则 1: 能力与内容分离

**Scaffold 提供能力，不承包所有内容。**

- ✅ 共享：schema、loader/writer、guard/preflight、policy/evidence
- ❌ 不共享：私有长期记忆内容、私有执行状态、私有 handoff

### 原则 2: 私有记忆隔离

**每个 Agent 的长期记忆内容必须私有。**

每个 Agent 至少实例化：
- `long_term_memory.yaml`
- `instruction_rules.yaml`
- `handoff_state.yaml`
- `execution_state.yaml`

### 原则 3: 高风险动作必须经过 Guard

**所有高风险动作都必须经过 Scaffold 的 guard / preflight / evidence。**

覆盖动作：
- 修改文件
- 更新状态
- 运行测试
- git push / rebase / merge / cherry-pick
- 关键任务切换

### 原则 4: 健康监控统一收口

**所有 Agent 的健康监控与恢复入口统一收口到 Scaffold。**

监控维度：
- session health
- task health
- memory health
- repo/workspace health

---

## 4. 记忆系统边界

### 启动读取顺序（强制）

每个 Agent 启动第一步必须按顺序读取：

1. `instruction_rules` → 确保后续恢复和执行受长期红线约束
2. `long_term_memory` → 补背景
3. `handoff_state` → 恢复工作交接点
4. `execution_state` → 恢复临时运行位置

### 记忆遵循机制

长期记忆与规则 **不是** prompt 拼接，而是执行前约束：

- `instruction_guard`
- `runtime_preflight`
- `mutation_guard`
- `repo/canonical guard`

**记忆不是参考，记忆是执行前约束的一部分。**

---

## 5. 禁止事项

| 禁止 | 原因 |
|------|------|
| 把所有 Agent 的记忆内容塞到同一个共享文件 | 会互相污染 |
| 只把长期记忆拼进 prompt | 不是启动恢复，也不是执行约束 |
| 只做记忆加载，不做写回 | 不会形成持久演化 |
| 只做 Session Bootstrap，不做 Runtime Guard | 会恢复，但执行时仍绕过规则 |
| 让各 Agent 各自私造一套 memory runtime | 会漂移，不可维护 |
| 把 Scaffold 做成业务大脑 | 它是底座，不是主体本体 |

---

## 6. 边界验证

### 如何判断职责是否越界

1. **问自己**：这个功能是"所有 Agent 都需要的运行保障"吗？
   - 是 → Scaffold 负责
   - 否 → 业务层负责

2. **问自己**：这个功能是"某个 Agent 特有的业务知识"吗？
   - 是 → Agent 私有记忆
   - 否 → 可考虑 Scaffold

3. **问自己**：这个功能是"用户交互/产品壳层"吗？
   - 是 → EgoCore
   - 否 → 继续

4. **问自己**：这个功能是"主体认知/情感/自我模型"吗？
   - 是 → OpenEmotion
   - 否 → 继续

---

## 7. 文档归属

| 文档类型 | 归属系统 |
|----------|----------|
| Memory/Execution/Health runtime 文档 | Scaffold |
| 产品功能文档 | EgoCore |
| 主体认知/情感文档 | OpenEmotion |
| Agent 私有记忆 | Agent 私有空间 |

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-17 | 初始版本，冻结边界 |

---

## 9. 参考

- `docs/MODULE_ARCHITECTURE.md` - 模块架构设计
- `docs/ARCHITECTURE_MODULE_MAPPING_A0.md` - 现有能力映射
