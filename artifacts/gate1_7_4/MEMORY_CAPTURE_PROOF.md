# MEMORY_CAPTURE_PROOF

Date: 2026-03-10

## Before config fix
Observed runtime failure during recall/capture:

```text
memory-lancedb: recall failed: Error: 404 404 page not found
memory-lancedb: capture failed: Error: 404 404 page not found
```

Root cause was the effective service config using:
- `baseUrl: http://192.168.79.1:11434`
instead of:
- `http://192.168.79.1:11434/v1`

## After config fix
The corrected gateway initialized successfully and recall started working.

However, for autoCapture specifically:
- no post-fix `auto-captured N memories` log was observed
- database row count remained `1`
- that single row is the manual proof row inserted through the same plugin dependency stack

## Database state observed
```text
ROWCOUNT 1
[
  {
    "id": "manual-proof",
    "text": "Remember this: I prefer dark mode",
    "category": "preference"
  }
]
```

## Interpretation
This proves:
- LanceDB storage layer works
- corrected embeddings path works
- plugin recall works against populated data

But it does NOT prove that post-fix autoCapture successfully wrote a new row from a real `agent_end` event.

## Honest status
AutoCapture success write is still not proven.
