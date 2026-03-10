# Final Report: OpenClaw main session context = unknown

## Executive Summary

**运行时行为层**: ✅ A-confirmed (Probe A/B 通过，continuity 正常)
**根因表述层**: ⏳ A-likely (需进一步核验 provider 原始响应)

**直接根因**: qianfan-code-latest 调用链上，OpenClaw 未拿到可用的 usage/token 统计
**上游候选**: provider usage 缺失 或 adapter/status 映射未透传

**功能状态**: 🟢 绿
**可观测性状态**: 🟡 黄
**严重级别**: Low
**是否阻塞主链**: No
**是否需要立刻修复**: No

---

## Investigation Summary

### 1. Baseline Collection ✅

| 检查项 | 结果 |
|--------|------|
| OpenClaw version | 2026.3.8 (3caab92) ✅ |
| Gateway status | running ✅ |
| Main session file | 存在，248 行 ✅ |
| Session continuity | 正常 ✅ |

### 2. Probe A/B Validation ✅

| Probe | 操作 | 结果 |
|-------|------|------|
| A | 记住随机串 | ✅ 通过 |
| B | 回忆随机串 | ✅ 正确回忆 |

**结论**: 主会话没坏，unknown 不是主链断裂

### 3. Usage Data Comparison

| Provider | API | input | output | totalTokens |
|----------|-----|-------|--------|-------------|
| qwen3:4b | - | 17854 | 571 | 18425 ✅ |
| glm-4.6 | - | 26145 | 249 | 26394 ✅ |
| **qianfan-code-latest** | **openai-completions** | **0** | **0** | **0** ❌ |

### 4. 核验: Adapter 层面

```
Session file 中的 message 结构:
- api: openai-completions
- provider: baiduqianfancodingplan
- model: qianfan-code-latest
- usage: {input: 0, output: 0, totalTokens: 0}
- rawResponse: 不存在
```

**关键发现**:
- usage 字段存在（adapter 有处理）
- 但值全为 0（上游未提供或未解析）
- 无 rawResponse 字段（无法直接核验原始响应）

---

## Root Cause Analysis

### 直接根因 (Confirmed)

> 当前 qianfan-code-latest 调用链上，OpenClaw 未拿到可用的 usage/token 统计，导致 `openclaw status` 显示 `unknown/200k`。

### 上游候选 (需进一步核验)

1. **Provider omission**: Baidu Qianfan 的 OpenAI 兼容 API 不返回 usage
2. **Adapter omission**: OpenClaw 的 baiduqianfancodingplan adapter 未正确解析 usage

**核验方法**: 抓取一次 qianfan API 的原始响应

---

## Impact Assessment

### 受影响
- `openclaw status` 显示 `unknown/200k (?%)`
- 可观测性体验下降（容易误判为 context 问题）

### 不受影响
- ✅ Session continuity
- ✅ Memory and context
- ✅ 对话功能
- ✅ 记忆能力

---

## Classification

| 层面 | 分类 | 置信度 |
|------|------|--------|
| 运行时行为 | A - 正常 | confirmed |
| 根因表述 | A - 可观测性缺口 | likely |

### Why Not Others

| Category | Reason |
|----------|--------|
| B - Session continuity | ❌ Probe A/B 验证正常 |
| C - Status parsing | ❌ 解析正确，数据是 0 |
| D - Recovery chain | ❌ 无恢复失败 |

---

## Recommendation

### 1. 归档为"观测缺口"

不应视为：
- continuity failure
- memory failure
- runtime blocker

应归类为：
- **Observability gap**
- provider usage 不可观测
- 状态显示缺口

### 2. 改进状态显示

将 `unknown/200k` 改为更准确的语义：
- `usage unavailable (provider did not report)`
- `N/A by provider`

避免误导为：
- continuity 坏了
- memory 丢了
- 快爆 context 了

### 3. 不需立刻修复

理由：
- 不影响功能
- Qianfan Coding Plan 是免费模型
- usage 统计意义有限

---

## Evidence Files

| File | Location |
|------|----------|
| Final Report | FINAL_REPORT.md |
| Classification | CLASSIFICATION.md |
| Fix Options | FIX_OPTIONS.md |
| Probe A | probes/probe_a.json |
| Probe B | probes/probe_b.json |

---

## 收口判断

**不用修 main 会话，不用碰 recovery / compaction / memory 主链。**

真正该做的是把它归档为"qianfan usage 不可观测导致的状态显示缺口"，避免以后被误报成上下文断裂。

---

Report Updated: 2026-03-10 00:25 UTC
Investigator: OpenClaw main agent
Classification: A-confirmed (runtime), A-likely (root cause)
