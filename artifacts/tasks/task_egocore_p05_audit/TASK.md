# Task: task_egocore_p05_audit

## Objective
P0.5 宿主化收口审计 - 确保 P0 接线成为谁都绕不过去的正式基础设施

## Repository
- Path: `/home/moonlight/Project/Github/MyProject/EgoCore`
- Branch: `main`

## Acceptance Criteria
1. contract 漂移被阻断 (versioning + compatibility guard)
2. adapter 越界被阻断 (boundary audit)
3. replay 可以承担回归保护 (regression suite)
4. 异常场景下主链可降级 (fallback policy)
5. Gate A/B/C 全部通过

## Steps
- [S1] Contract Versioning + Compatibility Guard
- [S2] Adapter Boundary Audit
- [S3] Replay Regression Suite
- [S4] Fallback / Degrade Policy
- [S5] Gate A/B/C 验证

## Status
- Created: 2026-03-16T02:12:46.752371Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
