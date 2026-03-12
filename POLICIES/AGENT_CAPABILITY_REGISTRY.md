# AGENT_CAPABILITY_REGISTRY

## Purpose
Registry of critical capabilities OpenClaw must maintain.

## Registered Capabilities

### CAP-HEARTBEAT_CYCLE_EXECUTION
- **Name**: Heartbeat Cycle Execution
- **Component**: heartbeat
- **Category**: liveness_capability
- **Expected Behavior**: Heartbeat runs successfully every cycle and produces OK/ALERT output
- **Verification Mode**: probe_check
- **Verification Frequency**: every_heartbeat_cycle
- **Severity if Missing**: critical
- **Degradation Rule**: No successful heartbeat in last 3 cycles

### CAP-CALLBACK_DELIVERY
- **Name**: Callback Delivery
- **Component**: callback-worker
- **Category**: delivery_capability
- **Expected Behavior**: Callbacks are delivered to correct targets with evidence
- **Verification Mode**: artifact_output_check
- **Verification Frequency**: 1h
- **Severity if Missing**: high
- **Degradation Rule**: No successful callback delivery in last 2h

### CAP-MAILBOX_CONSUMPTION
- **Name**: Mailbox Consumption
- **Component**: mailbox-worker
- **Category**: processing_capability
- **Expected Behavior**: Mailbox queue is consumed, no stuck messages
- **Verification Mode**: probe_check
- **Verification Frequency**: 30m
- **Severity if Missing**: high
- **Degradation Rule**: Queue backlog growing or stuck > 1h

### CAP-HEALTH_SUMMARY_GENERATION
- **Name**: Health Summary Generation
- **Component**: agent-health-summary
- **Category**: workflow_capability
- **Expected Behavior**: Health summary is generated with correct structure
- **Verification Mode**: artifact_output_check
- **Verification Frequency**: 1h
- **Severity if Missing**: medium
- **Degradation Rule**: No summary generated in last 2h

### CAP-INCIDENT_RECORDING
- **Name**: Incident Recording
- **Component**: agent-incident-report
- **Category**: safety_capability
- **Expected Behavior**: Incidents are recorded with proper schema
- **Verification Mode**: artifact_output_check
- **Verification Frequency**: on_demand
- **Severity if Missing**: high
- **Degradation Rule**: Incidents not persisting or schema invalid

### CAP-RECOVERY_SUMMARY_GENERATION
- **Name**: Recovery Summary Generation
- **Component**: agent-recovery-summary
- **Category**: workflow_capability
- **Expected Behavior**: Recovery summary reflects true effectiveness metrics
- **Verification Mode**: artifact_output_check
- **Verification Frequency**: 1h
- **Severity if Missing**: medium
- **Degradation Rule**: No summary or incorrect metrics in last 2h

### CAP-USER_PROMISED_FEATURE_TEMPLATE
- **Name**: User Promised Feature Template
- **Component**: agent-core
- **Category**: user_promised_feature
- **Expected Behavior**: Template slot for user-defined critical features
- **Verification Mode**: recent_success_check
- **Verification Frequency**: 24h
- **Severity if Missing**: high
- **Degradation Rule**: Feature not successfully executed in last 48h
- **Human Attention Required**: true
