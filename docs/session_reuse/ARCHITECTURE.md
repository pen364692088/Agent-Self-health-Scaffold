# Session Reuse / Thread Affinity v1.0 Architecture

## Goal
Prefer reusing the last active session for the same chat/thread/account without weakening Session Continuity recovery.

## Core rule
1. Try reuse first.
2. If reuse is not allowed, create/select a new session.
3. New session must still go through continuity recovery.

## Components
- `state/session_binding_registry.json` — durable binding registry
- `logs/session_decision_log.jsonl` — append-only decision log
- `tools/session_reuse_lib.py` — decision engine
- `tools/session-route` — CLI entrypoint for router integration

## Binding key
`chat_id::thread_id::account_id`

`thread_id` is normalized to `__default__` when absent.

## Reuse checks
A binding is reusable only if:
- binding exists
- same chat/thread/account
- `session_status != closed`
- within TTL
- `context_state != hard_blocked`
- session reference is valid when `session_file` is provided

## Decision outputs
- `selected_session_id`
- `reused`
- `reason`
- `previous_session_id`
- `recovery_needed`

## Current integration boundary
This v1.0 implements the decision layer and continuity handoff contract.
It does **not** patch OpenClaw core transport routing directly in this repo because no authoritative inbound router implementation is present here.
The intended attachment point is the earliest inbound routing layer before session creation.
