# AGENT_PROPOSAL_POLICY

## Purpose
Constrain medium-risk adjustments to proposal-only mode with shadow validation.

## Core Principle
Level B actions must only propose, never auto-execute.

## Proposal Types
- `timeout_adjustment`
- `retry_backoff_adjustment`
- `fallback_path_switch`
- `noncritical_hook_toggle`
- `watchdog_threshold_adjustment`
- `queue_policy_adjustment`
- `degraded_mode_entry`
- `capability_verification_frequency_adjustment`

## Required Fields
Every proposal must have:
1. Problem statement with evidence
2. Proposed change
3. Shadow validation plan
4. Success/failure metrics
5. Rollback plan

## Forbidden Actions
P3 proposals must NOT:
- Auto-execute
- Modify core governance files
- Change router/prompt/memory policy
- Bypass Gate validation
- Replace human approval

## Shadow Validation Contract
- Comparison window must be defined
- Baseline metrics must be captured
- Success threshold must be explicit
- Rollback trigger must be defined

## Status Flow
`pending -> in_review -> approved/rejected -> shadow_running -> completed`
