# Session Reuse Reason Enums

Fixed enums used by decision logic and logs:

- `reused_active_session`
- `no_active_binding`
- `idle_timeout`
- `thread_changed`
- `explicit_new_session`
- `context_limit`
- `session_closed`
- `agent_restart`
- `binding_invalid`
- `session_missing`
- `account_changed`
- `recovery_only_mode`

## Notes
- `reused_active_session` explicitly records successful reuse.
- `session_missing` is used when a binding points to a missing session file.
- `binding_invalid` is used for malformed timestamps or invalid session references.
- Some enums are reserved for upstream router wiring even if not emitted yet by the local CLI.
