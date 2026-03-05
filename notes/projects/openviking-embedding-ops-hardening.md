# OpenViking Embedding Ops Hardening

## Status
- Phase: P5 delivered; archive entry routing completed
- State: Active (manual operations mode, no cron)

## Latest
- Default archive entry switched to `scripts/openviking_archive_entry.py`.
- Legacy direct-write archive path is no longer the default workflow.
- Current policy from user: no new cron jobs.

## Key Artifacts
- `scripts/openviking_archive_entry.py`
- `scripts/openviking_backfill_embeddings.py`
- `scripts/openviking_embedding_healthcheck.py`
- `config/openviking_ops.yaml`

## Risks
- Without cron, regressions depend on manual checks.
- External direct `openviking add-resource` use can bypass guardrails.

## Next
- Maintain manual post-archive validation checklist.
- Enable minimal scheduled checks only if user later approves.
