---
name: manager-callback-gating
description: Enforce manager-side delivery gates and proactive callback push for multi-agent loops. Use when orchestrating coder/auditor rounds, waiting for subagent completion, or reporting milestone results where missed callbacks or false completion is risky.
---

# Manager Callback + Gating Skill

## Core policy
- Treat completion as valid only when all required gates pass.
- Do not rely on auto subagent completion visibility alone.
- Always send a proactive manager callback at key milestones.

## Mandatory gates (before declaring done)
1. Implementation commit hash is present.
2. Required evidence files exist and are readable.
3. Auditor verdict exists with final decision.

If any gate fails: status is BLOCKED with exact missing item.

## Callback contract
Send one concise proactive message with:
- `[Manager callback]`
- `runId=<id>`
- `status=done|blocked|approved`
- `payload:` short summary + key path(s)

## Role boundaries
- Coder: implementation only.
- Auditor: verdict only.
- Manager: orchestration, gate checks, user updates.

## Anti-failure defaults
- Prevent false done: verify artifact path existence before marking milestone complete.
- For high context load: write handoff snapshot to `memory/` and continue in fresh session.
