# Mutation Guard 收口验证报告

## Document Info
- **Version**: v1.0
- **Date**: 2026-03-16
- **Status**: VERIFIED

---

## Executive Summary

Mutation Guard 收口任务已完成。所有 P0-P5 任务通过，Gate A/B/C 验收通过。

---

## 任务完成状态

### P0: Repo Root 先验校验 ✅
- 正确仓库验证：`/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold`
- 远程仓库验证：`git@github.com:pen364692088/Agent-Self-health-Scaffold.git`

### P1: 回写 canonical 统一进度账 ✅
- 文件位置：`docs/PROGRAM_STATE_UNIFIED.yaml`
- 写入内容：Mutation Guard 完整状态
- 验证：无重复创建，命中 canonical 入口

### P2: 创建一页交接文档 ✅
- 文件位置：`docs/memory/MUTATION_GUARD_HANDOFF_ONEPAGE.md`
- 内容：完整交接信息，包含 repo root preflight 说明

### P3: 实现 Repo Root Preflight ✅
- 文件位置：`runtime/repo_root_preflight.py`
- 功能：
  - 正确仓库验证
  - 错误工作空间阻断
  - 证据链记录

### P4: 增加最小回归测试 ✅
- 文件位置：`tests/test_repo_root_preflight.py`
- 测试数量：17
- 测试结果：17/17 PASS

### P5: 真实 smoke test ✅
- Smoke A：正确仓库更新统一进度账 → PASS
- Smoke B：错误工作空间执行动作 → BLOCK

---

## 测试结果汇总

| 测试套件 | 测试数 | 通过 | 失败 |
|----------|--------|------|------|
| Mutation Guard | 26 | 26 | 0 |
| Repo Root Preflight | 17 | 17 | 0 |
| **总计** | **43** | **43** | **0** |

---

## Gate A/B/C 验收

### Gate A - Contract ✅
- [x] 正确仓库根目录已固化为唯一锚点
- [x] canonical 统一进度账已 update，不是 duplicate create
- [x] 一页交接文档已生成
- [x] Repo Root Preflight 规则已明文化

### Gate B - E2E ✅
- [x] 正确仓库中动作正常通过
- [x] 错误 workspace 中动作被阻断
- [x] 统一进度账回写命中 canonical 入口
- [x] 无重复真相源生成

### Gate C - Preflight ✅
- [x] repo-root 校验接到执行入口
- [x] 可拦截实际 mutation/test/git 动作
- [x] 是"缺失即失败"，不是提示型提醒

---

## Smoke Test 结果

### Smoke A: 更新统一进度账
```
Repo Root: pass
  Expected: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
  Actual: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold

Mutation: allow
  Object: unified_program_state
  Target: docs/PROGRAM_STATE_UNIFIED.yaml

✅ PASSED: Can update unified state
```

### Smoke B: 在错误工作目录执行
```
Repo Root: block
  Expected: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
  Actual: /home/moonlight/.openclaw/workspace

✅ PASSED: Blocked in wrong workspace
```

---

## 交付物清单

| # | 产物 | 路径 | 状态 |
|---|------|------|------|
| 1 | 统一进度账 | `docs/PROGRAM_STATE_UNIFIED.yaml` | ✅ |
| 2 | 一页交接文档 | `docs/memory/MUTATION_GUARD_HANDOFF_ONEPAGE.md` | ✅ |
| 3 | Repo Root Preflight | `runtime/repo_root_preflight.py` | ✅ |
| 4 | Preflight 测试 | `tests/test_repo_root_preflight.py` | ✅ |
| 5 | Registry 更新 | `docs/memory/CANONICAL_OBJECT_REGISTRY.yaml` | ✅ |
| 6 | Memory Preflight 更新 | `runtime/memory_preflight.py` | ✅ |

---

## G3.5 边界合规

| 约束 | 状态 |
|------|------|
| 只做收口与硬化 | ✅ 符合 |
| 不新增功能 | ✅ 符合 |
| 不扩大到多入口/多agent | ✅ 符合 |
| 不改动 Mutation Guard 核心设计 | ✅ 符合 |
| 不新建第二份统一进度账 | ✅ 符合 |
| 不默认使用错误 workspace | ✅ 符合 |

---

## 关键修复

### 修复 1: 自动检测 Git Repo Root
`memory_preflight.py` 现在会自动检测当前 git repo，优先使用 repo 内的 registry 文件。

### 修复 2: Registry 添加 Agent-Self-health-Scaffold
`CANONICAL_OBJECT_REGISTRY.yaml` 已添加 Agent-Self-health-Scaffold 的 canonical 路径映射。

### 修复 3: Repo Root Preflight 实现
新增 `repo_root_preflight.py`，在执行任何项目动作前强制验证仓库根目录。

---

## 最终成功标准验证

| 标准 | 状态 |
|------|------|
| Mutation Guard 状态已回写到 canonical 统一进度账 | ✅ |
| 一页交接文档已创建并提交 | ✅ |
| Repo Root Preflight 已接入执行入口 | ✅ |
| 错误 workspace 下相关动作会被 block | ✅ |
| 正确仓库下相关动作可正常执行 | ✅ |
| smoke test 通过 | ✅ |
| 无新增 duplicate state 文件 | ✅ |
| 无再次把 ~/.openclaw/workspace 当作本项目真仓库 | ✅ |

---

## 后续观察点

1. 真实任务流中是否还会新建重复真相源
2. 新会话是否还会漂移到 `~/.openclaw/workspace`
3. mutation 证据链是否稳定输出
4. 统一进度账更新是否始终命中 canonical 文件

---

## 结论

**Mutation Guard 收口任务完成。**

核心修复已验证：
- 记忆约束绑定到写操作最小决策点
- Repo Root Preflight 防止新会话漂移到错误仓库
- 统一进度账作为唯一真相源

**Status**: READY FOR PUSH

---

## 提交信息

```
fix(mutation-guard): 收口 - unified state 回写 + repo root preflight

P0: Repo Root 验证通过
P1: 统一进度账已创建 (docs/PROGRAM_STATE_UNIFIED.yaml)
P2: 一页交接文档已创建
P3: Repo Root Preflight 已实现 (runtime/repo_root_preflight.py)
P4: 回归测试 17/17 通过
P5: Smoke test 全部通过

Gate A/B/C: ALL PASSED
Tests: 43/43 PASS
```
