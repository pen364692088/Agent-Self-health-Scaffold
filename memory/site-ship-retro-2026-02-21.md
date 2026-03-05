# Site-ship Retro (2026-02-21)

## What worked
- Using `sessions_spawn` with tree visibility gave reliable child-agent execution and push-based completion updates.
- Separating roles improved outcomes:
  - Manager: orchestration + acceptance + status
  - Coder: implementation only
  - Auditor: verdict only
- Evidence-first verification (build/link/online checks) prevented false completion.

## What failed
- Manager overrode role boundary and implemented code directly (should delegate to coder).
- Claimed progress before hard evidence existed (caused trust/latency issues).
- Chased transcript files (`~/.openclaw/agents/.../sessions/*.jsonl`) as if they were executable config.
- Mailbox/cron handling was inconsistent; queue status was misreported.

## Rules to keep
1. Never declare completion without 3 proofs: artifact path, log/output, acceptance verdict.
2. For cron/mailbox: compute pending as `inbox - done` by id (never by file size/empty assumptions).
3. Treat round count as max cap, not success criteria; quality gates decide completion.
4. External-only blockers => `BLOCKED (needs user action)` with exact steps + re-check command.
5. Use milestone callbacks only when a real milestone is complete.

## Anti-patterns to avoid
- “I will do it now” without tool execution.
- Cross-tree session assumptions; always use current tree subagents.
- Verifier checks that ignore deployed subpath behavior (`/CVWebsite/`).

## Standard closeout checklist
- [ ] `evidence/build.log` refreshed
- [ ] `evidence/linkcheck.txt` refreshed
- [ ] `evidence/online-check.txt` refreshed with URL + key subpages
- [ ] `audit_final` generated with P0/P1/P2 + APPROVED/BLOCKED
- [ ] `MORNING_REPORT.md` exists in repo root
- [ ] mailbox out/done updated for queued milestones
