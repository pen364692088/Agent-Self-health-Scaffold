# Session Continuity Version Status

**Last Updated**: 2026-03-07

---

## Version Matrix

| Version | Release Date | Status | Score | Rollout |
|---------|--------------|--------|-------|---------|
| v1.1.1 | 2026-03-07 | STABLE | 92/100 | DEFAULT |
| v1.1 | 2026-03-07 | SUPERSEDED | 82/100 | BETA |
| v1.0 | 2026-03-07 | DEPRECATED | N/A | N/A |

---

## v1.1.1 (STABLE)

### Fixed Issues
- P0: Objective parser false "missing"
- P0: Field-level conflict resolution
- P1: Context ratio fallback

### Validation
- Gate A: PASS (9/9)
- Gate B: PASS
- Gate C: PASS (4/4)
- Scenarios: 6/6 PASS

### Recommendation
**DEFAULT BASELINE** for all new sessions

---

## v1.1 (SUPERSEDED)

### Known Issues
- Objective extraction unreliable
- File-level conflict resolution only
- Context ratio unstable

### Status
Do not use for new deployments. Migrate to v1.1.1.

---

## v1.0 (DEPRECATED)

### Status
Historical reference only. Not for production use.

---

## Migration Path

```
v1.0 → v1.1.1 (direct migration)
v1.1 → v1.1.1 (hotfix update)
```

No data migration required. State files compatible.