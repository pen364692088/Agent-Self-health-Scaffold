---
name: site-ship-manager-playbook
description: Manage site delivery loops with strict role boundaries (manager/coder/auditor), evidence gates, and deterministic mailbox status handling. Use when running site-ship style prose workflows, multi-agent delivery loops, or when progress/callback reliability is required.
---

# Site-Ship Manager Playbook

## Enforce roles
- Delegate all code/config edits to coder.
- Delegate all verdicts/risk grading to auditor.
- Keep manager focused on planning, orchestration, and acceptance gating.

## Required gates before completion
1. Implementation completed by coder (with commit hash).
2. Verification evidence refreshed:
   - `evidence/build.log`
   - `evidence/linkcheck.txt`
   - `evidence/online-check.txt`
3. Auditor verdict with P0/P1/P2 and final decision.

Completion rule:
- Self-fixable FAIL => P0 => not complete.
- External setting issue => `BLOCKED (needs user action)` + exact steps + re-check command.

## Mailbox reliability protocol
- Compute pending by id set difference: pending = inbox ids not in done ids.
- Select oldest pending by `created`/`createdAt`, fallback to line order.
- On process success, always do in order:
  1) write `mailbox/out/<id>.md`
  2) append done record `{id, finishedAt, source}`
  3) emit callback text

## Callback policy
- Send updates only on completed milestones.
- Every callback must include concrete proof (path/id/hash/status code).
- Never claim completion without evidence.

## Minimal manager loop
1. Spawn coder task with exact scope.
2. Spawn verifier task (or run deterministic checks).
3. Spawn auditor task for decision.
4. If verdict != APPROVED, send precise fix list to coder and iterate.
5. On completion, write final report (`MORNING_REPORT.md`) and provide artifact paths.
