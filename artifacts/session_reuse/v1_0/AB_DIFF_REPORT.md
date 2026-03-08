# Session Route Probe A/B Diff Report

## Samples

### Sample A — normal continuation baseline
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

### Sample B — wake-like new-session check
- inbound_event_id: telegram:7913
- probe_id: probe_375624225e882806_1772977825
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

## Direct answer

### Is it route input change?
**No evidence in this A/B pair.** The derived `session_key` stayed the same.

### Is it higher-layer runtime/UI rotation?
**No evidence in this A/B pair.** The runtime session id and session file path stayed the same. The reserved higher-layer surface fields are also unchanged/null.

### Is it only surface presentation difference?
**This A/B pair is most consistent with surface-only or no actual session rotation.** If the user experienced a “new session” feeling in this window, current evidence points away from route-key churn and away from runtime session-file rotation.

## Caveat
This compares two real same-chat direct-message samples from today (`7886` vs `7913`). It does not prove every historical wake-up case behaved identically; it proves this sampled pair does not show route-level or runtime-file-level churn.
