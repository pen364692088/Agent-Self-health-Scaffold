# GATEWAY_RESTART_AND_INIT_LOG

Date: 2026-03-10

## Restart / new init evidence
Observed new gateway/plugin init after config correction:

```text
Mar 10 00:21:54 ... memory-lancedb: plugin registered (db: /home/moonlight/.openclaw/memory/lancedb, lazy init)
Mar 10 00:21:56 ... memory-lancedb: initialized (db: /home/moonlight/.openclaw/memory/lancedb, model: mxbai-embed-large)
```

A later live process also injected memory into context, showing the corrected config was active in the running gateway.

## Meaning
This proves the plugin loaded successfully after restart and reached initialized state under the corrected service config.
