# 收口验证报告

**时间**: 2026-03-10 14:20 CST
**任务**: P0 高压触发验证 + Exact Provider 回归验证

---

## 验证结果总览

| 验证项 | 状态 | 证据 |
|--------|------|------|
| Gateway 生效 | ✅ PASS | Plugin 在真实请求链触发 |
| Plugin 接线 | ✅ PASS | before_prompt_build hook 正常工作 |
| 配置读取 | ✅ PASS | 从 openclaw.json 直接读取 threshold |
| 高压检测 | ✅ PASS | shouldCompact=true 被正确设置 |
| Compact 触发 | ❌ BLOCKED | OpenClaw API 无 triggerCompact 方法 |
| 主链路消费 | ❌ BLOCKED | event.needsCompact 未被主链路读取 |
| Exact Provider 回归 | ⏸️ SKIPPED | Provider 识别为 "unknown" |

---

## 关键发现

### 1. 高压检测已验证

**证据**:
```
[Context Guard] Provider: unknown, Tokens: 37588, Ratio: 18.8%
[Context Guard] Check: 0.1879 >= 0.001 = true
[Context Guard] ⚠️ HIGH PRESSURE! shouldCompact=true
```

Plugin 能够：
- 正确估算 token 数
- 正确计算 ratio
- 正确判断 shouldCompact

### 2. Compact 触发被阻断

**原因**: OpenClaw Plugin API 不提供 `triggerCompact` 方法

**可用 API**:
```
id, name, version, description, source, config, pluginConfig, 
runtime, logger, registerTool, registerHook, registerHttpRoute, 
registerChannel, registerProvider, registerGatewayMethod, 
registerCli, registerService, registerCommand, 
registerContextEngine, resolvePath, on
```

**尝试的方法**:
- `api.triggerCompact()` - 不存在
- `api.compact()` - 不存在
- `api.context?.compact()` - 不存在
- 返回 `{ needsCompact: true }` - 主链路不读取

### 3. 两套隔离系统

**OpenClaw 内置 context-compression**:
- 监听 `message:preprocessed`
- 自己计算 budget（基于 exact usage）
- 独立运行

**我们的 Plugin**:
- 监听 `before_prompt_build`
- 估算 tokens（针对 usage unknown provider）
- 设置标记但无法触发行为

### 4. Provider 识别问题

**现象**: Provider 字段始终为 "unknown"

**影响**:
- 无法区分 qianfan 和其他 provider
- Exact provider 回归验证无法进行
- 可能影响 provider 分支逻辑

---

## 验证结论

**状态**: STILL_PENDING

**原因**:
1. 高压检测 ✅ 但无法触发 compact ❌
2. Plugin 设置了 needsCompact=true 但主链路不读取
3. Provider 识别为 "unknown" 阻碍回归验证

---

## 风险等级

**中低 (medium-low)**

**依据**:
- ✅ 高压检测逻辑正确
- ✅ Plugin 已接入真实请求链
- ⚠️ 无法主动触发 compact
- ⚠️ 需要主链路集成才能生效

---

## 后续行动

### P1 - Provider 识别问题
单独开单跟踪 Provider: unknown 问题

### P0.5 - 主链路集成
需要 OpenClaw 核心：
1. 在 `before_prompt_build` 后检查 `event.needsCompact`
2. 或提供 `api.triggerCompact()` 方法
3. 或让 plugin 直接调用 context-compression 模块

### 验证清单状态
- [x] Gateway 生效验证
- [x] Plugin 接线验证
- [x] 高压检测验证
- [ ] Compact 触发验证 (BLOCKED)
- [ ] Exact Provider 回归验证 (SKIPPED)

---

**生成时间**: 2026-03-10 14:20 CST
