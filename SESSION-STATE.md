# SESSION-STATE.md

## 当前目标
**推进 v3 自治系统闭环验证与运行 - B0-4 完成**

## 阶段
**Phase B0 - 业务推进期（治理维护模式）**

### 当前进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| B0-1 现状盘点 | ✅ 完成 | 证据优先盘点，发现 steps 格式 bug、slot_registry 缺失 |
| B0-1.5 最小可运行链修复 | ✅ 完成 | 修复 steps 兼容、slot_registry stub、task_dossier 兼容层 |
| B0-2 最小闭环验证 | ✅ 完成 | S01 → S02 连续推进，minimal_executor 临时验证 |
| B0-3 真实执行器集成 | ✅ 完成 | StepExecutor + resume_execute_bridge，真实 shell 任务执行成功 |
| B0-4 恢复能力验证 | ✅ 完成 | pilot_b04_recovery_test 通过，S01→S02→S03 顺序执行成功 |

### 当前状态口径
**最小真实自治执行链已打通，恢复能力已验证。**
- 入口治理体系：**稳定治理状态** ✅
- 历史入口治理：已完成收口
- 增量入口治理：已建立
- 运行面残留：已完成收尾
- **当前治理债务已清零；后续治理转入增量纳管、回归守护与异常修复模式**

### 工作边界
**In Scope:**
- 基于现有治理基线的新功能开发
- 增量入口纳管
- 治理回退修复
- 回归增强

**Out of Scope（默认不做）:**
- 重做治理基础设施
- 重做历史入口全量治理
- 继续扩治理文档
- 制造不闭环的临时例外

### 治理触发条件
仅在以下情况重新进入治理专项模式：
- Level 3 漂移
- unresolved P0/P1 > 0
- registry/实现大面积失配
- 新入口绕过硬门禁
- 关键入口治理回退

## 分支
main

## Blocker
无

---

## 短观察阶段结论

**判定：PASS**

关键冷启动样本 #7 已通过。

/new 新会话下，session-start 入口层已先执行 Gate R0 Repo Root Guard。错误 repo/workspace 会被 BLOCK，后续执行仅允许在 canonical repo 中继续。

---

## 收口状态

| 层级 | 状态 | 说明 |
|------|------|------|
| 项目内执行层 | ✅ 已收口 | Mutation Guard 绑定到写操作最小决策点 |
| session-start 入口层 | ✅ 已收口 | Gate R0 Repo Root Guard 集成 |
| 唯一真相源 | ✅ 已收口 | Canonical repo root 明确定义 |
| 关键冷启动样本 #7 | ✅ 已通过 | 验证报告存档 |

---

## 系统级红线

**凡是涉及 Agent-Self-health-Scaffold 的任何会话启动、恢复、执行、测试、状态更新、git 操作，必须先通过 Gate R0 canonical repo guard；未命中唯一合法 repo root 时，一律不得继续。**

唯一合法 repo root:
```
/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
```

禁止替代:
```
/home/moonlight/.openclaw/workspace (OpenClaw 默认工作区，不是 Scaffold 项目仓库)
```

---

## Mutation Guard 完成状态

### P0: 根因落档 ✅
| 产物 | 路径 |
|------|------|
| 根因分析 | docs/memory/MEMORY_FAILURE_ROOT_CAUSE.md |
| 突变防护策略 | docs/memory/MUTATION_GUARD_POLICY.md |

### P1: Canonical Object Registry ✅
| 产物 | 路径 |
|------|------|
| 对象注册表 | docs/memory/CANONICAL_OBJECT_REGISTRY.yaml |

### P2: Memory Preflight ✅
| 产物 | 路径 |
|------|------|
| Preflight 实现 | runtime/memory_preflight.py |

### P3: Mutation Gate ✅
| 产物 | 路径 |
|------|------|
| Gate 实现 | runtime/mutation_gate.py |

### P4: 回归测试 ✅
| 产物 | 路径 |
|------|------|
| 测试套件 | tests/test_mutation_guard.py |
| 测试结果 | 26/26 通过 |

### P5: 证据链 ✅
| 产物 | 路径 |
|------|------|
| 验证报告 | artifacts/verification/MUTATION_GUARD_VERIFICATION_REPORT.md |
| 证据目录 | artifacts/mutations/ |

---

## Gate A/B/C 验收状态

| Gate | 状态 |
|------|------|
| Gate A - Contract | ✅ 通过 |
| Gate B - E2E | ✅ 通过 |
| Gate C - Preflight | ✅ 通过 |

---

## G3.5 边界合规

| 约束 | 状态 |
|------|------|
| 不新增功能 | ✅ 符合 |
| 不扩大到多入口/多agent | ✅ 符合 |
| 不做 full-on | ✅ 符合 |
| 仅修复阻塞主链 bug | ✅ 符合 |

---

## 下一步

1. **阶段决策**：B0 完成后，用户决策下一阶段方向
   - Phase 1: 多 worker 支持
   - Phase 2: 跨仓库任务依赖
   - Phase 3: subagent orchestration 集成
2. **提交证据**：当前有未提交的任务证据文件

---

## 红线状态

| 红线 | 值 |
|------|-----|
| Pending Receipts | ✅ 0 |
| Mutation Guard | ✅ ACTIVE |

---

## 更新时间
2026-03-16T19:25:00-05:00

---

## Session-Start Canonical Repo Guard 集成状态

**修复时间**: 2026-03-16T17:10:00-05:00

### 新增机制

1. **config/canonical_repos.yaml** - 定义唯一合法 repo root
   - Agent-Self-health-Scaffold: `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold`
   - 禁止替代: `~/.openclaw/workspace`

2. **tools/repo-root-guard** - Repo root 验证工具
   - 检测当前目录是否在 canonical repo
   - 返回 block 或 switch 指令

3. **session-start-recovery v1.2.0** - 集成 repo-root-guard
   - Gate R0: Repo Root Guard (MANDATORY)
   - 如果 wrong repo，返回 block 指令
   - Agent 必须切换到 canonical repo 后继续

### 验证要求

关键冷启动样本 #7 验证：
1. /new 新会话
2. 无人工干预
3. 第一次 Scaffold 相关任务
4. 先验证 repo root
5. 实际执行仅发生在 `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold`
