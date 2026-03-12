# Transferability Readiness Assessment

## Purpose
Framework for assessing whether a new instance is ready for scaffold integration.

## Assessment Categories

### 1. Instance Access (Required)
- [ ] Can access instance runtime
- [ ] Can create files in artifacts directory
- [ ] Can modify configuration if needed
- [ ] Can observe main loop behavior

**Status**: GO / NO-GO

### 2. Main Loop Visibility (Required)
- [ ] Can identify main loop entry point
- [ ] Can observe main loop timing
- [ ] Can add code to main loop
- [ ] Main loop is stable enough for monitoring

**Status**: GO / NO-GO

### 3. Worker Observability (High Priority)
- [ ] Can list all workers
- [ ] Can observe worker status
- [ ] Can access worker output
- [ ] Workers have identifiable progress signals

**Status**: READY / PARTIAL / NOT READY

### 4. Telemetry Potential (High Priority)
- [ ] Instance has some status output
- [ ] Status can be normalized to contract
- [ ] Can create new status outputs if needed
- [ ] No blocking architectural constraints

**Status**: READY / PARTIAL / NOT READY

### 5. Capability Clarity (Medium Priority)
- [ ] Can identify critical capabilities
- [ ] Capabilities have clear definitions
- [ ] Verification methods are feasible
- [ ] User-promised features are identifiable

**Status**: READY / PARTIAL / NOT READY

### 6. Integration Points (Medium Priority)
- [ ] Preflight/doctor entry exists
- [ ] Periodic scheduling exists
- [ ] Can add execution guards
- [ ] No conflicting monitoring systems

**Status**: READY / PARTIAL / NOT READY

## Readiness Levels

### Level 1: GO
- All required criteria met
- High priority criteria mostly ready
- Can proceed with integration

### Level 2: PARTIAL
- Required criteria met
- Some high/medium priority issues
- Can proceed with workarounds

### Level 3: NOT READY
- Required criteria not met
- Fundamental blockers exist
- Cannot proceed without resolution

## Assessment Template

Use this template for each new instance:

```markdown
# <INSTANCE_NAME> Readiness Assessment

## Date: YYYY-MM-DD

### Instance Access
- [ ] Can access runtime
- [ ] Can create files
- [ ] Can modify config
- [ ] Can observe behavior
**Status**: GO / NO-GO
**Notes**: 

### Main Loop Visibility
- [ ] Entry point identified
- [ ] Timing observable
- [ ] Can add code
- [ ] Loop is stable
**Status**: GO / NO-GO
**Notes**: 

### Worker Observability
- [ ] Workers listed
- [ ] Status observable
- [ ] Output accessible
- [ ] Progress signals exist
**Status**: READY / PARTIAL / NOT READY
**Notes**: 

### Telemetry Potential
- [ ] Status output exists
- [ ] Can normalize
- [ ] Can create new outputs
- [ ] No blocking constraints
**Status**: READY / PARTIAL / NOT READY
**Notes**: 

### Capability Clarity
- [ ] Capabilities identified
- [ ] Definitions clear
- [ ] Verification feasible
- [ ] Features identifiable
**Status**: READY / PARTIAL / NOT READY
**Notes**: 

### Integration Points
- [ ] Preflight exists
- [ ] Scheduling exists
- [ ] Guards possible
- [ ] No conflicts
**Status**: READY / PARTIAL / NOT READY
**Notes**: 

## Overall Readiness: Level 1 / Level 2 / Level 3

## Blockers
- [List any blockers]

## Workarounds
- [List workarounds if Level 2]

## Recommendations
- [Next steps]
```

## Quick Assessment Command

```bash
# Check basic readiness
echo "Instance Access:"
[ -w . ] && echo "  ✓ Can create files" || echo "  ✗ Cannot create files"

echo "Main Loop:"
[ -f "HEARTBEAT.md" ] && echo "  ✓ Heartbeat defined" || echo "  ? No HEARTBEAT.md"

echo "Telemetry:"
[ -d "artifacts/self_health/runtime" ] && echo "  ✓ Runtime dir exists" || echo "  ✗ No runtime dir"
```
