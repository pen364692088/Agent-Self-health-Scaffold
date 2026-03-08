# Wake-like Session Incident Report

## Conclusion
- level: **likely**
- verdict: **Likely surface-only presentation difference or no actual session rotation.**

## Current sample
- inbound_event_id: telegram:test-capture
- probe_id: probe_375624225e882806_1772978748
- route session_key: `agent:main:main`
- runtime_session_id: `20b82894-a9f6-40ef-acf0-b1e9362bf08d`
- session_jsonl_path: `/home/moonlight/.openclaw/agents/main/sessions/20b82894-a9f6-40ef-acf0-b1e9362bf08d.jsonl`
- session_file_name: `20b82894-a9f6-40ef-acf0-b1e9362bf08d.jsonl`
- created_at: `None`
- updated_at: `1772978678446`
- ui_conversation_id: `None`
- transport_conversation_id: `None`
- wrapper_session_id: `None`

## Baseline sample
- inbound_event_id: telegram:7886
- probe_id: probe_375624225e882806_1772977827
- route session_key: `agent:main:main`
- runtime_session_id: `20b82894-a9f6-40ef-acf0-b1e9362bf08d`
- session_jsonl_path: `/home/moonlight/.openclaw/agents/main/sessions/20b82894-a9f6-40ef-acf0-b1e9362bf08d.jsonl`
- session_file_name: `20b82894-a9f6-40ef-acf0-b1e9362bf08d.jsonl`
- created_at: `None`
- updated_at: `1772977630355`
- ui_conversation_id: `None`
- transport_conversation_id: `None`
- wrapper_session_id: `None`

## Diff result
- session_key_changed: **False**
- runtime_session_changed: **False**
- session_file_changed: **False**
- suspected_layer: **surface-only-or-none**
- suspected_cause: **surface_only_or_same_session**

## Changed fields
```json
{}
```

## Scope guard
This tool performs incident capture only.
It does not modify session routing, continuity state, or runtime behavior.
