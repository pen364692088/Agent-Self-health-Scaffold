# AGENT_CAPABILITY_CONTRACT

## Purpose
Ensure OpenClaw knows what capabilities it should have and can detect when they degrade or are forgotten.

## Core Principle
"Process alive" does not equal "capability exists".

## Capability Categories
- `liveness_capability`: Basic process/heartbeat
- `processing_capability`: Ability to process inputs
- `delivery_capability`: Ability to deliver outputs
- `memory_capability`: Ability to persist and recall
- `tooling_capability`: Ability to use specific tools
- `workflow_capability`: Ability to execute multi-step flows
- `safety_capability`: Ability to maintain safety boundaries
- `user_promised_feature`: Features explicitly promised to users

## Verification Modes
- `probe_check`: Check explicit state/metrics
- `synthetic_input_check`: Feed synthetic input, verify output
- `artifact_output_check`: Verify recent artifact production
- `recent_success_check`: Verify recent successful execution
- `chain_integrity_check`: Verify end-to-end chain works

## Degradation States
- `healthy`: Verified recently and working
- `stale`: Not verified recently
- `degraded`: Partially working
- `missing`: Not working at all
- `unknown`: Cannot determine

## Rules
1. Every critical capability must have a contract
2. Capabilities must be verified regularly
3. Degradation must be detected and reported
4. User-promised features must not be forgotten
5. Evidence must be machine-readable, not LLM opinion
