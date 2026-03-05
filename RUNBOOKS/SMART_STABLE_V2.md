# Smart+Stable v2 Runbook

## Goal
Improve intelligence (decision quality) and stability (recoverability) together.

## Per-task checklist
- [ ] Objective is testable (output + acceptance)
- [ ] Unknowns identified and resolved (or explicitly bounded)
- [ ] Primary path chosen
- [ ] Fallback path prepared
- [ ] Evidence collected before completion

## Routing policy
- Low complexity: default model
- Medium complexity: coding/specialized model
- High-risk ambiguity: high thinking + review loop

## Failure handling
1. Retry once with minimal mutation
2. Switch tool/transport strategy
3. Deliver minimum viable result with explicit risk note

## Completion policy
Do not mark complete unless evidence exists for:
- Correctness
- Edge conditions
- Security guardrails
- Rollback/recovery option
