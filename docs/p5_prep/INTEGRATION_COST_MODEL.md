# Integration Cost Model Template

## Purpose
Estimate effort required to integrate scaffold into a new instance.

## Cost Categories

### 1. Telemetry Integration

| Component | Low | Medium | High |
|-----------|-----|--------|------|
| Heartbeat telemetry | < 1 hour | 1-4 hours | > 4 hours |
| Worker telemetry (per worker) | < 30 min | 30 min - 2 hours | > 2 hours |
| Summary telemetry | < 1 hour | 1-4 hours | > 4 hours |
| Telemetry normalizer adaptation | < 2 hours | 2-8 hours | > 8 hours |

**Factors increasing cost**:
- No existing status output
- Non-standard status format
- Multiple workers to instrument
- Complex status semantics

### 2. Capability Overlay

| Component | Low | Medium | High |
|-----------|-----|--------|------|
| Overlay file creation | < 1 hour | 1-4 hours | > 4 hours |
| Capability definition (per cap) | < 15 min | 15 min - 1 hour | > 1 hour |
| User-promised feature registration | < 2 hours | 2-8 hours | > 8 hours |

**Factors increasing cost**:
- Many instance-specific capabilities
- Unclear capability boundaries
- Complex verification methods
- Need for custom verification logic

### 3. Scheduler Integration

| Component | Low | Medium | High |
|-----------|-----|--------|------|
| Quick mode wiring | < 30 min | 30 min - 2 hours | > 2 hours |
| Full mode wiring | < 30 min | 30 min - 2 hours | > 2 hours |
| Gate mode wiring | < 30 min | 30 min - 2 hours | > 2 hours |
| Lock/cooldown setup | < 15 min | 15 min - 1 hour | > 1 hour |

**Factors increasing cost**:
- No clear main loop entry point
- Complex scheduling requirements
- Need for custom execution budget

### 4. Gate Integration

| Component | Low | Medium | High |
|-----------|-----|--------|------|
| Gate A setup | < 15 min | 15 min - 1 hour | > 1 hour |
| Gate B validation | < 1 hour | 1-4 hours | > 4 hours |
| Gate C validation | < 1 hour | 1-4 hours | > 4 hours |
| Gate troubleshooting | < 2 hours | 2-8 hours | > 8 hours |

**Factors increasing cost**:
- Schema validation failures
- Capability state mismatches
- Summary generation issues

### 5. Validation & Soak

| Component | Low | Medium | High |
|-----------|-----|--------|------|
| Initial validation | < 1 hour | 1-4 hours | > 4 hours |
| Short soak (1-2 hours) | < 2 hours | 2-8 hours | > 8 hours |
| Extended soak (24 hours) | < 4 hours | 4-16 hours | > 16 hours |
| Issue resolution | < 4 hours | 4-16 hours | > 16 hours |

**Factors increasing cost**:
- Storm detection and fixing
- Main loop impact issues
- Capability truth mismatches

## Total Cost Estimation

### Low-Friction Instance
- Total: 8-16 hours
- Can reuse most components
- Standard telemetry
- Few instance-specific adaptations

### Medium-Friction Instance
- Total: 16-40 hours
- Some components need adaptation
- Non-standard telemetry
- Several instance-specific adaptations

### High-Friction Instance
- Total: 40+ hours
- Major adaptations required
- Custom telemetry adapters
- Many instance-specific adaptations

## Cost Tracking Template

Use this template when integrating a new instance:

```markdown
# <INSTANCE_NAME> Integration Cost

## Telemetry
- Heartbeat: X hours
- Worker 1: X hours
- Worker 2: X hours
- Summary: X hours
- Normalizer: X hours
- **Subtotal**: X hours

## Capability Overlay
- Overlay file: X hours
- Capabilities defined: X (X hours)
- User-promised features: X hours
- **Subtotal**: X hours

## Scheduler
- Quick mode: X hours
- Full mode: X hours
- Gate mode: X hours
- **Subtotal**: X hours

## Gate
- Gate A: X hours
- Gate B: X hours
- Gate C: X hours
- Troubleshooting: X hours
- **Subtotal**: X hours

## Validation
- Initial: X hours
- Soak: X hours
- Issue resolution: X hours
- **Subtotal**: X hours

## TOTAL: X hours

## Friction Classification: Low | Medium | High

## Blockers Encountered
- [List any blockers]
```
