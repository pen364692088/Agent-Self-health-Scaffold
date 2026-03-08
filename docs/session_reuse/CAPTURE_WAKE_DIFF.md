# capture-wake-session-diff

One-shot incident capture for wake-like session anomalies.

## Purpose
Capture evidence only:
- current probe
- nearest or explicit baseline sample
- automatic diff
- incident report with `confirmed` / `likely` / `inconclusive` conclusion

## Does not do
- no auto repair
- no session mutation
- no continuity mutation
- no runtime intervention

## Usage

```bash
tools/capture-wake-session-diff \
  --chat-id telegram:8420019401 \
  --account-id manager \
  --dm-scope per-channel-peer \
  --inbound-event-id telegram:7918
```

Optional explicit baseline:

```bash
tools/capture-wake-session-diff \
  --chat-id telegram:8420019401 \
  --account-id manager \
  --dm-scope per-channel-peer \
  --baseline artifacts/session_reuse/probe/real_samples/normal_continuation_7886.json
```

## Output
JSON with:
- `level`
- `verdict`
- `current_probe_path`
- `baseline_probe_path`
- `incident_report_path`
- `diff`

Incident reports are stored under:

```text
artifacts/session_reuse/incidents/
```
