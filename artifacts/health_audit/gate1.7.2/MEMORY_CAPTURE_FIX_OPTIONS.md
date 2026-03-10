# Memory Capture Fix Options

**日期**: 2026-03-09 23:15 CST

---

## 修复选项

### 方案 1: 检查并修复 KNOWN_TYPED_HOOK_NAMES

**优先级**: 高

**描述**: 确保 `agent_end` 在已知 hook 名单中

**步骤**:
1. 检查 `registry-D5r9Pc2H.js` 中的 KNOWN_TYPED_HOOK_NAMES
2. 如果不包含 `agent_end`，添加到名单

**风险**: 低

---

### 方案 2: 使用 hooks:loader 注册

**优先级**: 中

**描述**: 创建基于文件的 hook，绕过 api.on() 问题

**步骤**:
1. 创建 `~/.openclaw/hooks/memory-lancedb-capture/handler.ts`
2. 实现 agent_end 逻辑

**示例代码**:
```typescript
// ~/.openclaw/hooks/memory-lancedb-capture/handler.ts
export default async function handler(event, ctx) {
  if (!event.success || !event.messages) return;
  
  // 从消息中提取用户内容
  const userMessages = event.messages.filter(m => m.role === 'user');
  // ... capture 逻辑
}
```

**配置** (`~/.openclaw/hooks/memory-lancedb-capture/hook.json`):
```json
{
  "name": "memory-lancedb-capture",
  "event": "agent_end"
}
```

**风险**: 中（需要维护两套逻辑）

---

### 方案 3: 添加调试日志

**优先级**: 高

**描述**: 在 memory-lancedb 插件中添加调试日志

**步骤**:
1. 修改 `extensions/memory-lancedb/index.ts`
2. 在 `api.on("agent_end")` 开始添加日志

**示例代码**:
```typescript
api.on("agent_end", async (event) => {
  api.logger.info("memory-lancedb: agent_end hook triggered");
  
  if (!event.success) {
    api.logger.info("memory-lancedb: agent_end skipped, event.success=false");
    return;
  }
  
  // ... 现有逻辑
});
```

**风险**: 低

---

### 方案 4: 降级到 message 级别 capture

**优先级**: 低

**描述**: 使用 message:sending 或 reply_sent 级别的 hook 作为 fallback

**步骤**:
1. 注册 `api.on("message:sending", ...)`
2. 在消息发送时触发 capture

**风险**: 高（可能重复 capture）

---

### 方案 5: 手动 seed 工具

**优先级**: 中

**描述**: 创建手动 seed 工具，绕过 autoCapture

**步骤**:
1. 创建 `tools/memory-lancedb-manual-capture`
2. 直接调用 LanceDB API

**风险**: 低（仅用于验证）

---

## 推荐方案

### 短期（验证）

1. **方案 3**: 添加调试日志
2. **方案 5**: 创建手动 seed 工具

### 长期（修复）

1. **方案 1**: 检查 KNOWN_TYPED_HOOK_NAMES
2. **方案 2**: 使用 hooks:loader 注册
3. 向 OpenClaw 提交 bug report

---

## 立即可执行

### 创建 hooks:loader 版本

```bash
mkdir -p ~/.openclaw/hooks/memory-lancedb-capture
cat > ~/.openclaw/hooks/memory-lancedb-capture/hook.json << 'JSON'
{
  "name": "memory-lancedb-capture",
  "events": ["agent_end"]
}
JSON

cat > ~/.openclaw/hooks/memory-lancedb-capture/handler.ts << 'TS'
export default async function handler(event: any, ctx: any) {
  // Placeholder - 验证 hook 是否被触发
  console.log("memory-lancedb-capture hook triggered", event.success);
}
TS
```
