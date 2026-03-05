# Context Management Policy (approved by user)

Date: 2026-02-21

When main session context gets high (or child agents show similar pressure), apply this standard flow:

1. Persist current state before risk point
   - Write concise milestone/status to memory files and relevant report files.
   - Ensure artifact paths, verdict state, and pending tasks are recorded.

2. Shift execution to low-token orchestration
   - Keep main thread to milestone callbacks only.
   - Run implementation/verification/audit through spawned child agents.
   - Use mailbox queue for deterministic step-by-step continuation.

3. Rotate session safely when needed
   - Start a new session when context nears limit.
   - Resume from persisted state (memory + mailbox + bindings), not from long chat history.

4. Apply same policy to managed agents
   - If a child agent gets context-heavy, checkpoint and respawn with concise handoff.
   - Never block delivery waiting for context exhaustion.

This policy is mandatory for future runs unless user overrides it.
