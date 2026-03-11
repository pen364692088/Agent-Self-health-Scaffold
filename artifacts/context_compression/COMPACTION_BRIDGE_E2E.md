# Compaction Bridge E2E Test

**Version**: 1.0.0
**Date**: 2026-03-10
**Status**: IMPLEMENTED

---

## Test Objective

验证 Compaction Bridge 能够正确闭合 "检测高压 → 执行压缩" 的主链。

**核心验证点**:
1. Plugin 设置 `needsCompact=true` 被主链路正确消费
2. 高压时实际执行了 compact/summarize/trim
3. 压缩后压力回落或请求被安全阻断
4. Provider=unknown 场景记录为 P1 follow-up（本轮不处理）

---

## Implementation Status

### Phase 1: 保留 hook 压缩信号 ✅ DONE

**文件**: `src/plugins/types.ts`

**修改**: 扩展 `PluginHookBeforePromptBuildResult` 类型

```typescript
export type PluginHookBeforePromptBuildResult = {
  // ... existing fields ...

  // Compaction Bridge Fields
  needsCompact?: boolean;
  compactReason?: string;
  estimatedContextRatio?: number;
  contextPressureMode?: "estimated" | "exact";
};
```

### Phase 2: 实现 Compaction Bridge ✅ DONE

**文件**: 新建 `src/agents/pi-embedded-runner/compaction-bridge.ts`

**功能**:
- `checkAndTriggerCompaction()` - 主桥接函数
- 支持三种策略: compact, summarize, trim
- Cooldown 保护
- 最小消息数保护

### Phase 3: 在 reply 主链接入 bridge ✅ DONE

**文件**: `src/agents/pi-embedded-runner/run/attempt.ts`

**修改**:
1. 添加 import: `import { checkAndTriggerCompaction } from "../compaction-bridge.js";`
2. 在 `resolvePromptBuildHookResult` 返回中传递 compaction 字段
3. 在 hook 结果使用前调用 bridge

### Phase 4: Plugin 更新 ✅ DONE

**文件**: `~/.openclaw/extensions/context-guard/index.js`

**修改**: 设置标准 compaction bridge 字段

---

## Test Cases

### TC1: High Pressure Detection and Compaction

**目的**: 验证高压检测触发压缩

**前置条件**:
- context-guard plugin 已安装并配置
- threshold 设置为较低值（如 0.1）便于测试

**步骤**:
1. 发送多条消息累积 context
2. 触发 before_prompt_build hook
3. 检查日志确认:
   - `[Context Guard] HIGH PRESSURE!`
   - `[compaction-bridge] trigger`
   - `[compaction-bridge] compacted`

**预期结果**:
```
[Context Guard] Provider: xxx, Tokens: xxx, Ratio: xx.x%
[Context Guard] ⚠️ HIGH PRESSURE! ratio=xx.x% >= threshold=xx.x%
[Context Guard] Setting compaction bridge fields
[compaction-bridge] trigger sessionKey=xxx reason=context_pressure_high ratio=0.xx
[compaction-bridge] compacted sessionKey=xxx strategy=compact tokensBefore=xxx tokensAfter=xxx
```

### TC2: Cooldown Protection

**目的**: 验证 cooldown 机制防止重复压缩

**步骤**:
1. 触发第一次压缩
2. 立即发送第二条消息
3. 检查日志确认 cooldown 生效

**预期结果**:
```
[compaction-bridge] skipped: cooldown sessionKey=xxx
```

### TC3: Minimum Messages Guard

**目的**: 验证消息数不足时不触发压缩

**步骤**:
1. 创建新 session，只发送 2-3 条消息
2. 尝试触发压缩
3. 检查日志确认跳过原因

**预期结果**:
```
[compaction-bridge] skipped: insufficient_messages_3_5 sessionKey=xxx
```

### TC4: Strategy Fallback

**目的**: 验证策略回退机制

**步骤**:
1. 模拟 compact 方法不可用
2. 检查是否回退到 trim 策略

**预期结果**:
```
[compaction-bridge] strategy=compact failed, trying summarize
[compaction-bridge] compacted sessionKey=xxx strategy=trim
```

---

## Verification Commands

### 检查代码修改

```bash
# 检查类型扩展
grep -A 10 "Compaction Bridge Fields" ~/projects/openclaw-core/src/plugins/types.ts

# 检查 merge 函数
grep -A 5 "Compaction bridge fields" ~/projects/openclaw-core/src/plugins/hooks.ts

# 检查 bridge 文件
head -50 ~/projects/openclaw-core/src/agents/pi-embedded-runner/compaction-bridge.ts

# 检查主链调用
grep -B 2 -A 10 "Compaction Bridge" ~/projects/openclaw-core/src/agents/pi-embedded-runner/run/attempt.ts

# 检查 plugin 更新
grep -A 5 "Compaction Bridge Fields" ~/.openclaw/extensions/context-guard/index.js
```

### 运行日志监控

```bash
# 实时监控 compaction bridge 日志
journalctl --user -u openclaw-gateway -f | grep -E "Context Guard|compaction-bridge"
```

---

## Test Results

| Test Case | Status | Evidence |
|-----------|--------|----------|
| TC1: High Pressure Detection | ⏳ PENDING | 需要重新编译 OpenClaw |
| TC2: Cooldown Protection | ⏳ PENDING | 需要 E2E 测试环境 |
| TC3: Min Messages Guard | ⏳ PENDING | 需要 E2E 测试环境 |
| TC4: Strategy Fallback | ⏳ PENDING | 需要 E2E 测试环境 |

---

## Next Steps

1. **编译 OpenClaw 核心**
   ```bash
   cd ~/projects/openclaw-core
   npm run build
   ```

2. **安装更新后的版本**
   ```bash
   npm link
   ```

3. **重启 OpenClaw Gateway**
   ```bash
   openclaw gateway restart
   ```

4. **运行 E2E 测试**
   - 发送多条消息
   - 检查日志确认 bridge 触发

---

## Notes

- 本轮实现的是代码层面的 Bridge 接通
- E2E 验证需要重新编译和部署 OpenClaw
- Provider=unknown 问题已记录为 P1 follow-up
