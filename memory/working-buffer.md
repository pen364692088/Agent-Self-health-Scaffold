# Working Buffer

**Updated**: 2026-03-08T08:32:00-06:00

---

## Active Focus
把 Session Reuse / Thread Affinity v1.0 从“独立决策层”接到真正的 inbound router 上。

## What Exists Now
- `tools/session_reuse_lib.py` 提供 registry / decision log / TTL / reason enums
- `tools/session-route` 提供统一 CLI 入口
- 新 session 会返回 `recovery_needed=true`，可协同 continuity recovery
- 9 个核心测试已过

## What Is Missing
- 真实 transport/router 调用点
- 线上 reason 分布
- 真实 reuse 成功率
- 真实 recovery-after-new-session 数据

## Guardrails
- 不重写 continuity runtime
- 不改 WAL / handoff 语义
- 不做多候选复杂调度
- 先接单入口，再看是否扩展

## Next Actions
1. 找到 authoritative inbound router
2. 在 session 创建前调用 `session-route decide`
3. 只在 `recovery_needed=true` 时触发 recovery
4. 收集一轮真实日志后再调 TTL
