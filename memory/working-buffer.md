# Working Buffer

**Updated**: 2026-03-08T09:07:00-06:00

---

## Active Focus
Session Reuse / Thread Affinity v1.0 已进入观察态。当前重点不再是设计扩展，而是等待下一个真实 wake-like incident，并立即做现场取证。

## What Exists Now
- `tools/session-route-probe`: route/runtime probe + diff
- `tools/capture-wake-session-diff`: 一键现场取证
- incident 结论分级：
  - `confirmed`
  - `likely`
  - `inconclusive`
- real A/B report 已存在
- incident report 已存在一份当前样本结果

## Current Best Read
当前证据仍然最支持：
- surface-only presentation difference
- or no actual session rotation

而不是：
- route input churn
- runtime session/file rotation

## What To Do Next Time
一旦用户再次说“醒来像 new session”：
1. 立即运行 `tools/capture-wake-session-diff`
2. 保存 incident report
3. 看 level 是 confirmed / likely / inconclusive
4. 只有证据升级后再追更深层原因

## Guardrail
- 不自动修复
- 不自动干预 session
- 不改变 continuity/runtime
- 先取证，再判断
