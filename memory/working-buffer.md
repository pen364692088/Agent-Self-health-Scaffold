# Working Buffer

**Updated**: 2026-03-08T08:54:00-06:00

---

## Active Focus
把 session-route-probe 从“能看当前值”推进到“能做真实 A/B 证据对比”。这一轮已经完成。

## What Exists Now
- Probe 输出已包含：
  - `runtime_session_id`
  - `session_jsonl_path`
  - `session_file_name`
  - `created_at`
  - `updated_at`
  - `ui_conversation_id`
  - `transport_conversation_id`
  - `wrapper_session_id`
- Diff 输出已包含：
  - `session_key_changed`
  - `runtime_session_changed`
  - `session_file_changed`
  - `suspected_layer`
  - `suspected_cause`
- 已有两份真实样本：`7886` 与 `7913`
- 已有 A/B 报告：`artifacts/session_reuse/v1_0/AB_DIFF_REPORT.md`

## Current Best Read
这次真实 A/B 对比没有看到：
- route key 变化
- runtime session 变化
- session file 变化

因此当前最强结论不是“route churn”也不是“runtime rotation”，而是：
- surface-only presentation difference
- 或者根本没有实际 session rotation

## What Is Still Missing
- 一次真正命中“醒来像 new session”瞬间的 live probe
- higher-layer surface ids 的真实非空样本
- authoritative upstream source integration

## Next Actions
1. 下次症状一出现就立刻做 live probe
2. 拿 live pair 再跑一次 diff
3. 根据结果决定继续查 route 还是查 UI/control-plane session wrapper
