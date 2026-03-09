# Open Loops

- [ ] Decide whether to commit/push curated auto-tune reports (exclude oversized artifacts).
- [ ] Optional: promote `best_params_20260228_203016.json` to runtime default with rollback toggle.
- [x] MVP-5.1 D1–D4 + QA orchestration completed and pushed (`feature-emotiond-mvp`).
- [x] MVP-9 完整实现 + 评测通过 (0.9326 / 0.85, 24/24 场景).
- [x] OpenViking embedding 配置修复 (systemd --config 参数).
- [ ] 连续跟踪 7 天 Smart+Stable 指标；将 `avoidable_failure_count` 从 20 降到 <10。
- [x] OpenEmotion MVP-11 E2E+CI hardening：已完成并推送 `2d8a674`（E2E smoke + unified pipeline + soak profile + CI hardening），tool-gate 复检通过。
- [ ] OpenClaw 主会话超时优化：评估并决定是否设置 `agents.defaults.timeoutSeconds=900`。

- [x] OpenEmotion MVP-11.2：创建 PR 并附带 soak/effect-size 证据链接（PR #1，commit c04d3b3，分支已 push）。
- [x] 归档入口切换为 OpenViking hardened pipeline（`openviking_archive_entry.py`，commit `225fa98`）。
- [ ] 在“无 cron”约束下建立手动归档后健康检查清单（覆盖 metrics/policy/coverage）。
- [x] OpenEmotion MVP11.3.2：nightly dashboard + 7-day trend（heatmap/sparkline/drift）已落地并写入 Actions summary。
- [ ] 连续观察 7 次 nightly trend，确认 sentinel 轮换下 Gate 波动是否稳定可解释。
- [ ] 评估是否加 scenario-split trend（baseline/focused/wide 分层）以减少轮换噪声误判。

## 2026-03-08
- Native compaction safeguard bug remains OPEN.
- Next step: apply/verify root fix in actual live runtime path and revalidate native compaction end-to-end.
- Phase D / Natural Validation remains BLOCKED pending real live compaction success evidence.

- [ ] Compaction safeguard lane blockage: identify what is holding `agent:main:telegram:direct:8420019401` session lane and why queued `/compact` work is not draining.
- [ ] Post-adoption live revalidation: after lane blockage is cleared, rerun minimal native compaction check and distinguish semantic correction vs functional restoration.
