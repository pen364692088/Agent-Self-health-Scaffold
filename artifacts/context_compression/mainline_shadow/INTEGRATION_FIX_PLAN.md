# MAINLINE SHADOW INTEGRATION FIX PLAN

## 目标
修复 OpenClaw 主流程中 Context Compression Shadow 的"文档已定义、代码未调用"问题。

## 问题诊断

### 当前状态
- SHADOW_MANIFEST.json 已定义集成点
- context-budget-check 工具已存在
- context-compress 工具已存在
- context-retrieve (anchor-aware-retrieve) 工具已存在
- **但主流程代码从未调用这些工具**

### 根因
- 集成点只存在于文档/manifest 中
- OpenClaw Gateway 和 pi-coding-agent 代码中没有实际调用

## 修复策略

### Hook 接入点分析

**Option A: Gateway 层接入**
- 位置: OpenClaw Gateway (gateway-cli-vk3t7zJU.js)
- 优点: 统一入口，易于管理
- 缺点: 需要修改 OpenClaw 核心代码

**Option B: Agent Session 层接入**
- 位置: pi-coding-agent (agent-session.js)
- 优点: 接近 prompt 构建逻辑
- 缺点: 需要修改底层依赖

**Option C: Wrapper/Middleware 层接入**
- 位置: 创建 wrapper 脚本
- 优点: 不修改核心代码，易于测试
- 缺点: 需要额外的调用层

### 推荐方案: Option C (Wrapper 层)

创建 `mainline-shadow-hook` wrapper，在 Gateway 调用 agent 之前插入 hooks。

## 实现步骤

### Phase 1: 创建 Hook Wrapper
1. 创建 `tools/mainline-shadow-hook` 脚本
2. 实现 feature flag 检查
3. 实现 kill switch 检查
4. 实现 budget-check 调用
5. 实现 shadow compress 调用
6. 实现 anchor-aware-retrieve 调用

### Phase 2: 集成到主流程
1. 找到 Gateway 调用 agent 的位置
2. 在调用前插入 hook wrapper
3. 确保 feature flags 生效
4. 确保 kill switch 继续有效

### Phase 3: Runtime Counters
1. 创建计数器文件
2. 在 hooks 中增加计数
3. 提供查询接口

### Phase 4: Smoke Test
1. 运行 3 个 low-risk 会话
2. 验证 counters 增长
3. 验证真实回复未被修改
4. 验证 kill switch 仍然有效

## 边界约束

- ❌ 不修改旧 S1 baseline
- ❌ 不修改 patch set 本身
- ❌ 不修改 scoring/metrics/schema
- ❌ 不进入 enforced 模式
- ❌ 不扩大到高风险会话
- ❌ 不改变真实回复
- ❌ 不写回 active session

## 验收标准

1. budget_check_call_count > 0
2. sessions_evaluated_by_budget_check > 0
3. 至少出现以下之一:
   - sessions_over_threshold > 0
   - compression_opportunity_count > 0
   - shadow_trigger_count > 0
4. real_reply_modified_count = 0
5. active_session_pollution_count = 0
6. kill_switch 状态 = PASS

## 时间线

- Phase 1: 30 分钟
- Phase 2: 20 分钟
- Phase 3: 15 分钟
- Phase 4: 15 分钟

**预计总时间**: 80 分钟
