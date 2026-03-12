# Agent-Self-health-Scaffold v2

A constrained self-healing execution kernel scaffold for OpenClaw.

## Why this exists
The problem is not lack of monitoring. The problem is that after restart, corruption, or partial failure, the system often cannot continue the task automatically.

This project focuses on five primary execution-chain goals:
1. durable task truth via a ledger
2. restart-time automatic recovery
3. out-of-band restart execution
4. transcript rebuild from execution truth
5. durable parent/child subtask orchestration

## Current phase
**Scaffold / architecture phase**

Included in this repository now:
- v2 architecture docs
- recovery and repair policies
- initial failure taxonomy
- JSON schemas for task/run/repair/ledger
- directory structure for core/runtime/pipelines/tests/artifacts

## P0 build order
1. task ledger
2. state materializer
3. recovery orchestrator
4. out-of-band restart executor
5. transcript rebuilder
6. durable job orchestrator

## Key rule
Task truth is primary; transcript is derived.
