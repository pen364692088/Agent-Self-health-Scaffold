# Second-Instance Onboarding Checklist

## Purpose
Step-by-step guide for integrating Agent Self-Health Scaffold into a new OpenClaw instance.

## Prerequisites

- [ ] Target instance is a real OpenClaw instance
- [ ] Access to instance runtime environment
- [ ] Ability to create files in artifacts directory
- [ ] Basic understanding of instance's workers and main loop

## Phase 1: Baseline Assessment

### 1.1 Instance Information
- [ ] Record instance name/identifier
- [ ] Document runtime environment (OS, Node version, etc.)
- [ ] Identify main loop entry point
- [ ] Identify heartbeat mechanism
- [ ] List active workers

### 1.2 Worker Inventory
- [ ] List all workers by name
- [ ] Document worker responsibilities
- [ ] Identify worker status output locations
- [ ] Note any special worker behaviors

### 1.3 Current State
- [ ] Document current health monitoring (if any)
- [ ] List known issues
- [ ] Identify critical capabilities to protect
- [ ] Note instance-specific user_promised_features

## Phase 2: Telemetry Integration

### 2.1 Heartbeat Telemetry
Create: `artifacts/self_health/runtime/heartbeat_status.json`

Required fields:
- [ ] last_heartbeat_at (ISO timestamp)
- [ ] heartbeat_lag_seconds (number)
- [ ] heartbeat_cycle_ok (boolean)
- [ ] heartbeat_status ("ok"|"warning"|"error")

### 2.2 Worker Telemetry
For each critical worker, create status file with:
- [ ] worker_name
- [ ] alive (boolean)
- [ ] last_progress_at (ISO timestamp)
- [ ] stuck_suspected (boolean)
- [ ] worker_status ("ok"|"warning"|"error")

### 2.3 Summary Telemetry
Create: `artifacts/self_health/runtime/summary_status.json`
- [ ] last_health_summary_at
- [ ] last_recovery_summary_at
- [ ] summary_pipeline_status

## Phase 3: Capability Overlay

### 3.1 Create Overlay File
Create: `POLICIES/<INSTANCE>_CAPABILITY_OVERLAY.md`

### 3.2 Register Capabilities
For each critical capability:
- [ ] Define capability_id (CAP-*)
- [ ] Specify expected_behavior
- [ ] Set verification_mode
- [ ] Set verification_frequency
- [ ] Set severity_if_missing
- [ ] Define degradation_rule

### 3.3 User-Promised Features
Register 1-3 real instance features:
- [ ] Feature has meaningful name
- [ ] Feature has verification method
- [ ] Feature has degradation rule
- [ ] Feature is not just template placeholder

## Phase 4: Scheduler Integration

### 4.1 Quick Mode
- [ ] Identify heartbeat entry point
- [ ] Add quick check call
- [ ] Verify execution budget < 30s
- [ ] Test lock mechanism

### 4.2 Full Mode
- [ ] Identify periodic schedule entry
- [ ] Add full cycle call
- [ ] Verify execution budget < 120s
- [ ] Test cooldown

### 4.3 Gate Mode
- [ ] Identify preflight/doctor entry
- [ ] Add gate check call
- [ ] Verify Gate A/B/C execution
- [ ] Test integration

## Phase 5: Validation

### 5.1 Initial Capability Check
- [ ] Run capability check
- [ ] Verify telemetry_missing vs missing distinction
- [ ] Check capability states make sense

### 5.2 Gate Validation
- [ ] Run Gate A check
- [ ] Run Gate B check
- [ ] Run Gate C check
- [ ] Document any PARTIAL/FAIL reasons

### 5.3 Soak Test
- [ ] Run quick mode for multiple cycles
- [ ] Run full mode at least once
- [ ] Run gate mode at least once
- [ ] Monitor for storms
- [ ] Check main loop impact

## Phase 6: Documentation

### 6.1 Instance-Specific Docs
- [ ] Create baseline document
- [ ] Create telemetry adaptation report
- [ ] Document instance differences
- [ ] Note any instance-specific adaptations

### 6.2 Metrics Collection
- [ ] Collect capability metrics
- [ ] Collect incident/proposal metrics
- [ ] Collect gate metrics
- [ ] Collect main loop impact metrics

## Completion Criteria

Minimum for STABLE_WITH_CAVEATS:
- [ ] At least 1 telemetry source working
- [ ] At least 1 capability registered
- [ ] At least 1 scheduler mode working
- [ ] No incident/proposal storms
- [ ] Main loop impact acceptable

For INSTANCE_PROVEN:
- [ ] All critical telemetry sources working
- [ ] Gate A/B/C all PASS
- [ ] At least 1 user_promised_feature verified
- [ ] Soak test completed
- [ ] No structural issues found
