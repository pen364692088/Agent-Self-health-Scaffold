# OPERATION_RUNBOOK.md

## Operator checks
- confirm ledger is writable
- confirm recovery scan runs on boot
- confirm restart executor is out-of-band
- confirm transcript rebuild is non-authoritative
- confirm duplicate execution guard is active

## Emergency fallback
If recovery loops or repeated repair failure occur:
1. mark run blocked
2. preserve ledger
3. capture repair trial artifacts
4. stop auto-repair on that run
5. require human review
