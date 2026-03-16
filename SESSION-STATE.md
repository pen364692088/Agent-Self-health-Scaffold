# SESSION-STATE.md

## 当前目标
✅ 短观察阶段 PASS - Mutation Guard + Repo Root Preflight + Session-Start Canonical Repo Guard 主线级闭环完成

## 阶段
Phase A3 - 已闭环，进入冻结维护

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

1. **集成**：将 mutation gate 接入现有写操作流程
2. **监控**：观察 evidence logs 是否有异常 block
3. **扩展**：根据需要添加更多 canonical objects

---

## 红线状态

| 红线 | 值 |
|------|-----|
| Pending Receipts | ✅ 0 |
| Mutation Guard | ✅ ACTIVE |

---

## 更新时间
2026-03-16T16:00:00-05:00

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
   - 如果 wrong repo，返回 block 消息
   - Agent 必须切换到 canonical repo 后继续

### 验证要求

关键冷启动样本 #7 验证：
1. /new 新会话
2. 无人工干预
3. 第一次 Scaffold 相关任务
4. 先验证 repo root
5. 实际执行仅发生在 `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold`

