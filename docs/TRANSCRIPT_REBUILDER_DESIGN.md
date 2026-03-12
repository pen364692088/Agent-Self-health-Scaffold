# TRANSCRIPT_REBUILDER_DESIGN.md

## Goal
Ensure task continuity even if transcript ordering, compaction, or tool-call pairing is corrupted.

## Design
- ledger remains source of execution truth
- transcript materializer rebuilds user-facing history from ledger events plus selected chat artifacts
- ordering normalization happens at rebuild time
- orphaned transcript data may be dropped if it cannot be reconciled to ledger truth

## Rebuild outputs
- normalized transcript
- repair report
- linkage map from ledger events to transcript entries

## Safety rule
Transcript repair may improve readability, but must never rewrite ledger truth.
