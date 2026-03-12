# E2E_TEST_MATRIX.md

## E2E-01 gateway restart auto-resume
Expect unfinished eligible runs to resume without manual "continue".

## E2E-02 recover from last-good-step
Expect completed steps not to replay after mid-step failure.

## E2E-03 transcript corruption isolation
Expect task progression to continue from ledger even if transcript is rebuilt.

## E2E-04 missing child recovery
Expect lost child job to be requeued or reconciled without duplication.

## E2E-05 failed high-risk repair rollback
Expect failed repair to rollback or downgrade without polluting run truth.

## E2E-06 unattended long-run completion across restart
Expect end-to-end task completion across process restart and watcher interruption.
