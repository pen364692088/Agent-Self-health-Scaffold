# Session Route Probe / Diff

## Purpose
Separate two questions with evidence:

1. Did the derived `sessionKey` change?
2. Did the runtime session identity change?

## Tool

```bash
tools/session-route-probe probe \
  --chat-id telegram:8420019401 \
  --account-id manager \
  --dm-scope per-channel-peer
```

Artifacts are written under:

```text
artifacts/session_reuse/probe/
```

## Diff two probes

```bash
tools/session-route-probe diff --left left.json --right right.json
```

## Output shape
- `route_inputs`
- `route_inputs_hash`
- `route.session_key`
- `route.main_session_key`
- `runtime.runtime_session_id`
- `runtime.runtime_session_matches`
- `heuristics.reused_channel_slot`
- `heuristics.new_runtime_session_created`
- `heuristics.suspected_cause`

## Suspected cause heuristics
- `suspected_route_input_change`
- `suspected_thread_change`
- `suspected_account_change`
- `suspected_runtime_rotation`
- `unknown`

## Notes
The probe uses the installed OpenClaw `session-key` dist module to derive the same session-key logic used upstream, instead of reimplementing it by hand.
