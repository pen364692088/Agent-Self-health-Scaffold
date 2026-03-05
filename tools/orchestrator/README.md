# Subagent Callback Reliability System

This system upgrades the main agent task progression from "wait for callback-driven" to a "main-controlled Join/Poll-driven + optional explicit receipt + fallback mailbox" approach.

## Problem
Current main agents spawn subagents and wait for callbacks/announces to continue. However, in some conditions, subagents complete their tasks but callbacks are lost/delayed, causing main tasks to stall until the user sends another message.

## Solution
- **Join/Poll Mechanism**: Main agent actively polls for subagent completion
- **Explicit Receipts**: Optional structured callbacks from subagents
- **File Mailbox Fallback**: Subagents write completion files as persistence
- **State Machine**: Track subtasks through their lifecycle

## Architecture
- SPAWN → PENDING → JOIN(POLL) → COLLECT → CONTINUE
- Supports parallel subagents with unified sync point
- Timeout/retry/escalation strategies
- Audit trail for all operations