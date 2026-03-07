# LIGHT_ENFORCED MANIFEST

**Version**: 1.0
**Started**: 2026-03-07 08:37 CST
**Status**: ACTIVE

## 启动条件验证

| 前提条件 | 状态 |
|----------|------|
| 旧 S1 baseline 保持有效 | ✅ |
| 新 baseline 已成立 | ✅ |
| Mainline shadow 已接入 | ✅ |
| 真实 trigger 已验证 | ✅ |
| real_reply_modified = 0 | ✅ |
| active_session_pollution = 0 | ✅ |
| Kill switch 可用 | ✅ |

## Feature Flags

```
CONTEXT_COMPRESSION_ENABLED=1
CONTEXT_COMPRESSION_MODE=light_enforced
CONTEXT_COMPRESSION_BASELINE=new_baseline_anchor_patch
```

## 覆盖范围

### 允许的会话类型
- 单主题日常聊天
- 非关键任务
- 非复杂工具链上下文

### 排除的会话类型
- 高风险执行任务
- 多 agent 关键协作
- 复杂代码修复链
- 多文件路径密集调试
- 高价值/高风险决策会话

## 行为说明

**Light Enforced vs Shadow**:

| 行为 | Shadow | Light Enforced |
|------|--------|----------------|
| 预算检查 | ✅ | ✅ |
| 压缩执行 | 仅记录 | **真实生效** |
| 上下文修改 | ❌ | ✅ |
| 审计记录 | ✅ | ✅ |
| 回退能力 | ✅ | ✅ |

## 回退触发器

| 条件 | 动作 |
|------|------|
| real_reply_corruption > 0 | IMMEDIATE ROLLBACK |
| active_session_pollution > 0 | IMMEDIATE ROLLBACK |
| kill_switch 失效 | IMMEDIATE ROLLBACK |
| replay guardrail 恶化 | INVESTIGATE |
| continuity signal 异常 | INVESTIGATE |

## 不变约束

- ❌ 不修改旧 S1 baseline
- ❌ 不修改 scoring/metrics/schema
- ❌ 不扩大 patch set
- ❌ 不加入 prompt assemble anchor 注入
- ❌ 不关闭 replay guardrail
- ❌ 不关闭 admissibility audit
- ❌ 不改变高风险会话行为
- ❌ 不移除 kill switch

## 观察窗口

- **持续时间**: 72 小时
- **最小会话数**: 20
- **最大会话数**: 50
- **扩大条件**: 稳定 + 无异常

---

**启动人**: Manager Agent
**启动时间**: 2026-03-07 08:37 CST
