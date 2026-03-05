# Task: MVP11.2 Soak + Effect Size + CI Guard

## Context
Use handoff doc `交接文档_20260304_OpenEmotion_MVP11_AEGIS---4b56a673-7796-4cb7-a60b-8c94143a3819.md` as source of truth.
Current status: MVP11 + hardening done; next phase is MVP11.2 production/science reliability.

## Objective
Implement and validate MVP11.2 in OpenEmotion repo:
1) Long-run soak runner
2) Effect-size evaluator for P1~P4 interventions
3) CI guard to prevent replay determinism drift

## Scope (must do)
- Add `scripts/soak_mvp11.py`
  - run 10k ticks (and configurable up to 100k)
  - emit metrics json + concise markdown summary
  - metrics at least: memory growth, log growth, focus switch rate, replan rate, governor intercept rate, homeostasis drift
- Add `scripts/effects_mvp11.py`
  - fixed seeds, repeated runs, per-intervention effect size output for P1~P4
  - output `reports/mvp11_effects.json` + markdown table
- Ensure trace-driven replay protections in CI
  - add/ensure deterministic replay tests in CI workflow
  - fail on regression

## Constraints
- Follow existing anti-drift contract and no-report evidence style.
- Keep changes minimal and composable.
- Include exact commands to run and expected output artifacts.

## Acceptance Criteria
- New scripts exist and run without crashing.
- Tests for determinism/replay are in CI required path.
- One command sequence can regenerate soak + effects artifacts.
- Provide final changed file list and risk notes.
