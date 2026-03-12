# PILOT_INSTANCE_CAPABILITY_OVERLAY

## Purpose
Instance-specific capability definitions for moonlight-VMware-Virtual-Platform.

## Base Capabilities (Inherited)
All capabilities from AGENT_CAPABILITY_REGISTRY.md are inherited.

## Instance-Specific Capabilities

### CAP-USER_PROMISED_FEATURE_TELEGRAM_NOTIFICATION
- **Name**: Telegram Notification Delivery
- **Component**: telegram-channel
- **Category**: user_promised_feature
- **Expected Behavior**: Telegram messages are delivered to configured targets
- **Verification Mode**: recent_success_check
- **Verification Frequency**: 1h
- **Severity if Missing**: high
- **Degradation Rule**: No successful message delivery in last 2h
- **Human Attention Required**: true

### CAP-USER_PROMISED_FEATURE_SUBAGENT_ORCHESTRATION
- **Name**: Subagent Orchestration
- **Component**: subtask-orchestrate
- **Category**: user_promised_feature
- **Expected Behavior**: Subagent tasks can be spawned and completed
- **Verification Mode**: recent_success_check
- **Verification Frequency**: 6h
- **Severity if Missing**: medium
- **Degradation Rule**: No successful subagent completion in last 12h
- **Human Attention Required**: true

### CAP-USER_PROMISED_FEATURE_MEMORY_PERSISTENCE
- **Name**: Memory Persistence
- **Component**: memory
- **Category**: memory_capability
- **Expected Behavior**: Session memory is persisted to memory/ directory
- **Verification Mode**: artifact_output_check
- **Verification Frequency**: 24h
- **Severity if Missing**: medium
- **Degradation Rule**: No memory files written in last 48h

## Adjusted Frequencies
- CAP-HEARTBEAT_CYCLE_EXECUTION: every heartbeat cycle (unchanged)
- CAP-CALLBACK_DELIVERY: 30m (increased from 1h)
- CAP-MAILBOX_CONSUMPTION: 15m (increased from 30m)

## Temporarily Disabled
- None at this time
