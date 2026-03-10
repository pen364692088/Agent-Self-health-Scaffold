# R3 Phase 2B Design

Date: 2026-03-10
Status: PLANNING
Priority: P1 (观察窗结束后执行)

---

## 设计约束

1. **不修改默认路由逻辑**（Phase 2B 只做设计，不实施）
2. **不修改工具选择优先级**
3. **不合并会改变 runtime 行为的入口**
4. **设计需经用户确认后执行**

---

## 优先级排序

| 优先级 | 变更 | 影响范围 | 实施风险 |
|--------|------|----------|----------|
| **P1** | D1: 统一记忆检索路由 | 中 | 低 |
| **P1** | D3: 状态写入入口统一 | 中 | 低 |
| P2 | D2: 子代理创建入口收口 | 高 | 中 |
| P2 | D6: 回执处理流程简化 | 中 | 中 |
| P3 | D5: Heartbeat 流程优化 | 低 | 低 |
| - | D4: Memory-Lancedb 增强 | 中 | 待评估 |

---

## D1: 统一记忆检索路由

### 当前状态

```
用户请求记忆
    │
    ├── session-query (推荐主入口)
    │     └── sqlite3 session_index.db + openviking fallback
    │
    ├── context-retrieve (S1 专用)
    │     └── capsule + openviking L2
    │
    ├── session-start-recovery (自动调用)
    │     └── 内部检索逻辑
    │
    └── openviking find (底层)
          └── 直接查询向量索引
```

### 问题

1. `session-query` 和 `context-retrieve` 职责重叠
2. `session-start-recovery` 有独立检索逻辑，可能不一致
3. 用户不确定何时用哪个入口

### 设计方案

**Option A: session-query 增强**

```python
# session-query 内部集成 context-retrieve 逻辑
def session_query(query, mode="auto"):
    if mode == "auto":
        # 自动选择最佳检索策略
        if is_context_compression_active():
            return context_retrieve(query)  # L1 + L2
        else:
            return simple_search(query)     # sqlite + openviking
    elif mode == "l1":
        return capsule_lookup(query)
    elif mode == "l2":
        return openviking_find(query)
```

**Option B: 路由代理**

```python
# 新增 memory-router 作为统一入口
def memory_router(query, context=None):
    if context == "session_start":
        return session_start_retrieval(query)
    elif context == "compression":
        return context_retrieve(query)
    else:
        return session_query(query)
```

**Option C: 保持现状，仅文档对齐**

- 维持现有入口
- 强化文档指引
- 不改变任何行为

### 推荐

**Option A (渐进式)**:
1. 在 `session-query` 添加 `--mode` 参数
2. 内部调用 `context-retrieve` 或简单检索
3. 保持 `context-retrieve` 作为独立工具（S1 专用）
4. 更新 `session-start-recovery` 使用 `session-query`

### 实施步骤

1. 为 `session-query` 添加 `--mode` 参数（非破坏性）
2. 更新 `session-start-recovery` 调用 `session-query`
3. 更新文档推荐
4. 观察 3 天，确认无回归

### 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| session-start-recovery 行为变化 | 中 | 高 | 添加回退开关 |
| 检索结果不一致 | 低 | 中 | 添加对比测试 |
| 性能下降 | 低 | 低 | 性能基准测试 |

---

## D3: 状态写入入口统一

### 当前状态

```
状态写入请求
    │
    ├── safe-write (推荐主入口)
    │     └── policy-eval → 原子写入
    │
    ├── safe-replace (推荐主入口)
    │     └── policy-eval → 内容替换
    │
    └── state-write-atomic (专用)
          └── 直接原子写入（无策略检查）
```

### 问题

1. `state-write-atomic` 绕过 Execution Policy
2. 两套写入系统可能不一致
3. `state-write-atomic` 用于 SESSION-STATE.md，但缺少策略保护

### 设计方案

**Option A: state-write-atomic 内部调用 safe-write**

```python
# state-write-atomic 内部实现
def state_write_atomic(path, content):
    # 对 ~/.openclaw/** 路径，调用 safe-write
    if path.startswith("~/.openclaw"):
        return safe_write(path, content)
    else:
        # 其他路径，直接原子写入
        return direct_atomic_write(path, content)
```

**Option B: safe-write 添加 SESSION-STATE 专用模式**

```python
# safe-write 添加专用模式
def safe_write(path, content, mode="normal"):
    if mode == "session_state":
        # SESSION-STATE 专用：强制原子写入 + WAL 记录
        return atomic_write_with_wal(path, content)
    else:
        return normal_safe_write(path, content)
```

**Option C: 合并为单一工具**

- 移除 `state-write-atomic`
- 所有状态写入通过 `safe-write`
- 添加 `--atomic` 参数

### 推荐

**Option A (最小变更)**:
1. `state-write-atomic` 内部调用 `safe-write`
2. 保持两个工具对外接口不变
3. 统一策略检查

### 实施步骤

1. 修改 `state-write-atomic` 内部实现
2. 添加集成测试
3. 验证 SESSION-STATE.md 写入行为
4. 观察 3 天，确认无回归

### 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 策略检查阻止合法写入 | 低 | 高 | 白名单机制 |
| 性能下降 | 低 | 低 | 性能基准测试 |
| 状态持久化失败 | 极低 | 极高 | 回退开关 |

---

## D2: 子代理创建入口收口

### 当前状态

```
子代理创建请求
    │
    ├── subtask-orchestrate (推荐主入口)
    │     └── sessions_spawn + 回执管理
    │
    ├── spawn-with-callback (调试)
    │     └── sessions_spawn + 回调设置
    │
    └── sessions_spawn (底层 API)
          └── 直接创建子代理
```

### 设计方案（延后）

**原因**: 需用户确认迁移计划

**初步设计**:
1. `spawn-with-callback` 添加弃用警告
2. 更新内部调用使用 `subtask-orchestrate`
3. 设置弃用时间表

---

## 实施优先级

### 观察窗结束后 (Week 1)

| 顺序 | 变更 | 预计耗时 |
|------|------|----------|
| 1 | D1: session-query 增强 | 2-3 小时 |
| 2 | D3: state-write-atomic 集成 | 1-2 小时 |
| 3 | 集成测试 | 2 小时 |
| 4 | 观察 3 天 | - |

### 观察窗结束后 (Week 2)

| 顺序 | 变更 | 预计耗时 |
|------|------|----------|
| 1 | D2: 弃用警告（如用户确认） | 1 小时 |
| 2 | D6: 回执流程简化设计 | 2-3 小时 |
| 3 | D5: Heartbeat 优化设计 | 1-2 小时 |

---

## 验收标准

### D1 验收

- [ ] `session-query --mode auto` 返回与 `context-retrieve` 一致结果
- [ ] `session-start-recovery` 使用 `session-query`
- [ ] 无检索结果差异
- [ ] 无性能回归

### D3 验收

- [ ] `state-write-atomic` 通过 Execution Policy 检查
- [ ] SESSION-STATE.md 写入成功
- [ ] WAL 记录正确
- [ ] 无状态丢失

---

## 回滚计划

### D1 回滚

```bash
# 恢复 session-query 原始行为
git checkout HEAD~1 -- tools/session-query
git checkout HEAD~1 -- tools/session-start-recovery
systemctl --user restart openclaw-gateway
```

### D3 回滚

```bash
# 恢复 state-write-atomic 原始行为
git checkout HEAD~1 -- tools/state-write-atomic
systemctl --user restart openclaw-gateway
```

---

## 下一步

1. ✅ Phase 2B 设计完成
2. ⏳ 等待观察窗结束
3. ⏳ 用户确认 D1/D3 实施
4. ⏳ 执行变更
5. ⏳ 验收测试

