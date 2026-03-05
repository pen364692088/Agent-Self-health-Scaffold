# OpenEmotion MVP-11 E2E + CI Hardening

## Status
- Delivery complete + pushed to `feature-emotiond-mvp`; pending optional PR creation and long-run evidence enrichment.

## Completed
- Verified tool-gate sweep + tool_doctor + done-guard + pytest/tests/mvp11 + mvp11_e2e(ci) all pass.
- Added cross-process API smoke script (`tools/e2e_api_smoke_mvp11.sh`).
- Added unified pipeline (`scripts/mvp11_e2e.py`) with final summary artifact.
- Parameterized full soak (`scripts/run_full_intervention_soak.py`) for `ci/full` profiles.
- Added CI workflow (`.github/workflows/mvp11-hardening.yml`) for PR quick gate + nightly full gate.
- Added replay fallback logic for non-ledger `science_run_id` cases.

## Local Commits
- `2d8a674` — feat(mvp11): add E2E smoke, unified pipeline, soak profiles, and CI hardening (pushed)
- `381fdfe` — mvp11: add e2e smoke, unified pipeline, and ci/nightly hardening gates
- `7a675b8` — mvp11_e2e: add replay fallback for non-ledger science run ids

## Risks
- Model timeout on long embedded runs (10m boundary observed).
- Provider capability mismatch if fallback uses unsupported coding-plan profile.

## Next Step
- Open PR from `feature-emotiond-mvp`，附 `reports/mvp11_effects.json` 与 soak 结果。
- 在 CI/nightly 跑 10k/100k soak 并补充效应量对比（mock vs full planner）。

- `fb42dfe` — feat(mvp11.2): add effect-size eval and replay determinism CI gate

## MVP11.2 Cycle-Closure Evidence Layer (2026-03-04)
- 分支：`feature-emotiond-mvp-cycle-evidence`
- 提交：`c04d3b3`
- PR：`https://github.com/pen364692088/OpenEmotion/pull/1`
- 交付：cycle observability + soak/effect size 接入 + intervention sensitivity tests
- 待办：补 10k/100k soak 统计证据并评估将 cycle 指标纳入 CI gate

### Archive Follow-up (2026-03-04 22:27 CST)
- 已执行会话归档二次确认。
- 已将 MVP11.2 归档摘要迁移到顶层仓库并推送：`de7efff`。
- 备注：顶层 `.openclaw` 仓库忽略 `workspace*/`，后续继续采用“摘要迁移”策略。

## MVP11.3 / MVP11.3.1 / MVP11.3.2 (2026-03-05)
- **C3 policy**: keep OFF (evidence-first, distribution-level gating before enable).
- **Delivered**:
  - `266063c` — MVP11.3 C0/C1/C2 (cycle invariant fix + candidates + consolidation store)
  - `458bb00` — MVP11.3.1 (distribution soak profile + gate evaluator + nightly gate workflow)
  - `cf11047` — MVP11.3.2 phase A (sentinel weekday rotation + dashboard summary publishing)
  - `10820d4` — MVP11.3.2 phase B (7-day trend export/builder/fetch + summary integration)
- **Current nightly outputs**:
  - `artifacts/mvp11/dashboard/nightly_dashboard.{json,md}`
  - `artifacts/mvp11/trends/trend_entry.json`
  - `artifacts/mvp11/trends/trend_7d.{json,md}`
- **Operational note**: trend is soft-observe layer (no hard fail by default), gate logic remains authoritative.
