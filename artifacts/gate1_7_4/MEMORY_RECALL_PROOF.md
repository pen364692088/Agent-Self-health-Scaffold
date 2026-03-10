# MEMORY_RECALL_PROOF

Date: 2026-03-10

## Empty -> populated evidence
Initially the DB directory contained only:
- `gate1_7_seed_marker.json`

Later it contained real LanceDB table files:

```text
/home/moonlight/.openclaw/memory/lancedb/memories.lance/data/...
/home/moonlight/.openclaw/memory/lancedb/memories.lance/_transactions/...
/home/moonlight/.openclaw/memory/lancedb/memories.lance/_versions/...
```

## Runtime recall evidence
After config correction, gateway logs changed from repeated 404 failures to successful recall injection:

```text
Mar 10 00:23:09 ... memory-lancedb: injecting 1 memories into context
Mar 10 00:23:11 ... memory-lancedb: injecting 1 memories into context
...
Mar 10 00:28:34 ... memory-lancedb: injecting 1 memories into context
```

## In-conversation proof
A later inbound message arrived with injected memory context:

```text
[preference] Remember this: I prefer dark mode
```

That is direct evidence that recall no longer behaves like an empty-table 404 path.

## Conclusion
- LanceDB is populated: YES
- recall path works: YES
- empty-table 404 state persists: NO
