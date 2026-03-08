# Handoff Summary

**Created**: 2026-03-08T08:54:00-06:00

---

## Current Objective
继续推进 session-route-probe，优先做真实 A/B diff，不再停留在抽象设计。

## What Was Completed
- session-route-probe 已增强，输出：
  - runtime_session_id
  - session_jsonl_path
  - session_file_name
  - created_at
  - updated_at
  - ui_conversation_id
  - transport_conversation_id
  - wrapper_session_id
- diff 已增强，输出：
  - session_key_changed
  - runtime_session_changed
  - session_file_changed
  - suspected_layer
  - suspected_cause
- 准备了两份真实样本：
  - `artifacts/session_reuse/probe/real_samples/normal_continuation_7886.json`
  - `artifacts/session_reuse/probe/real_samples/wake_like_new_session_7913.json`
- 跑出了真实 A/B diff 并生成报告：
  - `artifacts/session_reuse/v1_0/AB_DIFF_REPORT.md`

## Main Finding
在这组真实样本里：
- session_key 没变
- runtime_session_id 没变
- session_file 没变

所以当前证据更支持：
- surface-only presentation difference
- 或 no actual session rotation

而不是：
- route input change
- higher-layer runtime rotation

## Test Status
- `pytest -q tests/session_reuse/test_session_route_probe.py tests/session_reuse/test_session_reuse_v1.py`
- 12 passed

## Commits to remember
- `7803f58` Add session route probe and diff tooling
- next commit in this handoff includes enriched probe fields + real A/B report

## Resume Path
1. Read `artifacts/session_reuse/v1_0/AB_DIFF_REPORT.md`
2. Read `docs/session_reuse/ROUTE_PROBE.md`
3. If the symptom happens again, run live probe immediately and diff against prior sample
