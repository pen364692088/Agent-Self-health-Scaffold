# Mutation Guard 修复交接（一页版）

## 结论
Mutation Guard 已在正确仓库完成、验证并推送，核心问题已从"记忆可参考"升级为"写操作前强制门禁"。

- **正确仓库**：`/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold`
- **远程**：`git@github.com:pen364692088/Agent-Self-health-Scaffold.git`
- **提交**：`164aa7e`

---

## 本次修的真问题

不是"没做记忆"，而是：

1. **记忆约束未绑定到写操作最小决策点**
2. **canonical target resolution 不强制**
3. **update_only 无法阻止 create**
4. **新会话可能漂移到错误仓库 / 默认 workspace**

---

## 已完成修复

### 机制层

- **Canonical target resolution**：强制执行
- **update_only**：阻止 create duplicate
- **ambiguity = block**：不猜路径、不自作主张
- **mutation evidence chain**：每次突变留证据

### 交付物

| 文件 | 路径 |
|------|------|
| 根因分析 | `docs/memory/MEMORY_FAILURE_ROOT_CAUSE.md` |
| 防护策略 | `docs/memory/MUTATION_GUARD_POLICY.md` |
| 对象注册表 | `docs/memory/CANONICAL_OBJECT_REGISTRY.yaml` |
| Preflight | `runtime/memory_preflight.py` |
| Gate | `runtime/mutation_gate.py` |
| 测试 | `tests/test_mutation_guard.py` |
| 验证报告 | `artifacts/verification/MUTATION_GUARD_VERIFICATION_REPORT.md` |
| 统一进度账 | `docs/PROGRAM_STATE_UNIFIED.yaml` |

### 验收

| Gate | 状态 |
|------|------|
| Gate A / Contract | ✅ PASS |
| Gate B / E2E | ✅ PASS |
| Gate C / Preflight | ✅ PASS |
| Regression tests | ✅ 26/26 PASS |

---

## 这次额外确认出的关键经验

**上一个会话即使说过正确仓库并已归档，`/new` 新会话后系统仍可能回到默认工作空间：**

```
~/.openclaw/workspace
```

**这说明：**

> "会话归档过" ≠ "新会话执行时一定命中正确 repo root"

**因此后续必须增加并执行 Repo Root Preflight。**

---

## Repo Root Preflight（强制）

凡涉及本项目的以下动作：

- 读写文件
- 跑测试
- rebase / merge / cherry-pick
- push
- 更新统一进度账

**第一步必须先确认：**

```bash
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
```

**期望唯一仓库根目录必须是：**

```
/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
```

**若不是该路径：**

- ❌ 立即停止当前动作
- ❌ 不允许继续 mutation / rebase / push
- ✅ 先切回正确仓库后再执行

---

## 后续观察点

1. 真实 smoke test 中是否还会新建重复真相源
2. 新会话是否还会漂移到 `~/.openclaw/workspace`
3. mutation 证据链是否稳定输出
4. 统一进度账更新是否始终命中 canonical 文件

---

## 一句话红线

**凡是涉及 Agent-Self-health-Scaffold 的执行动作，先验 repo root，再做任何写操作。**

---

## 快速参考

```bash
# 正确仓库
cd /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold

# 验证位置
git rev-parse --show-toplevel
# 期望输出: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold

# 查看统一进度账
cat docs/PROGRAM_STATE_UNIFIED.yaml

# 运行测试
python3 tests/test_mutation_guard.py
```
