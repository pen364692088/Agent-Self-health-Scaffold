# Capability Overlay Template

## Purpose
Instance-specific capability definitions that extend or override base registry.

## Overlay File
Create: `POLICIES/<INSTANCE_NAME>_CAPABILITY_OVERLAY.md`

## Template Structure

```markdown
# <INSTANCE_NAME> Capability Overlay

## Base Capabilities (Inherited)
All capabilities from AGENT_CAPABILITY_REGISTRY.md are inherited.

## Instance-Specific Capabilities

### CAP-<INSTANCE>_<FEATURE_NAME>
- **Name**: Human-readable name
- **Component**: System component
- **Category**: liveness_capability | processing_capability | delivery_capability | memory_capability | tooling_capability | workflow_capability | safety_capability | user_promised_feature
- **Expected Behavior**: What this capability should do
- **Verification Mode**: probe_check | synthetic_input_check | artifact_output_check | recent_success_check | chain_integrity_check
- **Verification Frequency**: How often to verify
- **Severity if Missing**: critical | high | medium | low
- **Degradation Rule**: When to consider degraded
- **Fallback if Missing**: What to do if missing (optional)

## Adjusted Frequencies
- CAP-*: Adjusted frequency for this instance

## Temporarily Disabled
- CAP-*: Reason for disabling

## Instance-Specific Notes
- Any special considerations
```

## Example Overlay

```markdown
# Production_Instance Capability Overlay

## Instance-Specific Capabilities

### CAP-USER_PROMISED_FEATURE_DAILY_REPORT
- **Name**: Daily Report Generation
- **Component**: report-generator
- **Category**: user_promised_feature
- **Expected Behavior**: Generate daily summary report by 6am UTC
- **Verification Mode**: artifact_output_check
- **Verification Frequency**: 24h
- **Severity if Missing**: high
- **Degradation Rule**: No report generated in last 48h
- **Human Attention Required**: true
```

## Guidelines

### User-Promised Features
- Must be real instance features, not placeholders
- Must have verification method
- Must have degradation rule
- Should align with actual instance behavior

### Frequency Adjustments
- Faster for critical capabilities
- Slower for stable, low-risk capabilities
- Consider instance rhythm

### Severity Assignment
- critical: Instance cannot function without this
- high: Significant user impact
- medium: Noticeable but not critical
- low: Nice to have
