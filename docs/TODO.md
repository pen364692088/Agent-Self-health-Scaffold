# TODO.md - v2 Main-Chain TODO

## Done this session
- [x] E2E-01 gateway restart auto-resume
- [x] E2E-02 failed step retry from last-good-step context
- [x] E2E-03 transcript rebuild from ledger after corruption/deletion
- [x] Add minimal reconciler (`scan -> apply`)
- [x] Add `recovery_apply.py`
- [x] Wire restart executor to apply recovery instead of scan-only
- [x] Register pytest `e2e` mark

## Next main-chain work
- [ ] E2E-04 child job missing -> requeue exactly once
- [ ] E2E-05 high-risk repair -> gate fail -> rollback
- [ ] E2E-06 unattended long task across multiple restarts
- [ ] Periodic recovery apply worker / daemon loop
- [ ] Promote apply-path evidence into docs/INTERFACE_FREEZE.md and E2E matrix
- [ ] Replace transcript rebuilder `datetime.utcnow()` with timezone-aware UTC call

## Non-goals for now
- [ ] Cosmetic report/dashboard polish
- [ ] Broad cleanup of historical self-health artifacts
- [ ] Expanding watcher/shadow layers before main-chain closure
