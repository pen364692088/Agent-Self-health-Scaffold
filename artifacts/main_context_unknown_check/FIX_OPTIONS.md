# Fix Options: context = unknown

## 根因

qianfan-code-latest 调用链上，OpenClaw 未拿到可用的 usage/token 统计。

---

## Option 1: 归档为观测缺口 (推荐)

**描述**: 将此问题归档为"可观测性缺口"，不是故障。

**理由**:
- 不影响功能
- Continuity 正常
- Qianfan Coding Plan 是免费模型

**实施**:
- 标记为 "Observability gap"
- 不作为 blocker
- 文档说明

---

## Option 2: 改进状态显示语义

**描述**: 把 `unknown/200k` 改成更准确的语义。

**改进方向**:
```
现状: unknown/200k (?%)
建议: usage unavailable (provider did not report)
     或 N/A by provider
```

**好处**:
- 避免误导（不是 continuity 坏了）
- 状态表达更准确
- 降低误报

**实施位置**: OpenClaw `status` 命令的显示逻辑

---

## Option 3: 核验 Provider 原始响应

**描述**: 抓取 qianfan API 原始响应，确认是 provider 不返回还是 adapter 丢字段。

**方法**:
1. 启用 debug 日志
2. 发起一次 qianfan 调用
3. 检查原始响应中是否有 usage 字段

**判定**:
- 原始响应无 usage → confirmed: provider omission
- 原始响应有 usage → confirmed: adapter omission

**实施**: 需要修改 OpenClaw 或增加日志

---

## Option 4: 切换到有 usage 的模型

**描述**: 如果需要精确 usage 统计，切换到其他 provider。

**选项**:
- qwen3:4b (返回 usage ✅)
- glm-4.6 (返回 usage ✅)

**代价**: 可能需要付费，或模型能力不同

---

## Option 5: 修改 Adapter (不推荐)

**描述**: 修改 OpenClaw 的 baiduqianfancodingplan adapter。

**前提**:
- 确认 Qianfan API 返回 usage (需 Option 3 核验)
- 找到正确的 usage 字段映射

**风险**: 如果 API 不返回，无法修复

---

## 推荐顺序

1. **Option 1**: 归档为观测缺口 (优先)
2. **Option 2**: 改进状态显示语义 (可选)
3. **Option 3**: 核验原始响应 (如需精确根因)
4. **Option 4**: 切换模型 (如需精确 usage)
5. **Option 5**: 修改 adapter (不推荐，成本高)

---

## 不推荐的操作

- ❌ 清 session / 重启 (不是数据问题)
- ❌ 修改 sessions.json 结构 (格式正确)
- ❌ 触发 compaction (不是 context 溢出)
- ❌ 修复 recovery chain (没有断)

---

## 收口建议

**不用修 main 会话，不用碰 recovery / compaction / memory 主链。**

归档为 "qianfan usage 不可观测导致的状态显示缺口"，避免被误报成上下文断裂。

---

Last Updated: 2026-03-10 00:25 UTC
