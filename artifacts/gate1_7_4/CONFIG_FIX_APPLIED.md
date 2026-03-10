# CONFIG_FIX_APPLIED

Date: 2026-03-10

## What was wrong
The gateway actually reads `~/.openclaw/openclaw.json`, not `~/.openclaw/config.json`.
The effective memory-lancedb config in `openclaw.json` had:

- `baseUrl: http://192.168.79.1:11434`
- plugin type: OpenAI-compatible embeddings client

That base URL is wrong for OpenAI-compatible embeddings and produced 404s.
It must be:

- `baseUrl: http://192.168.79.1:11434/v1`

## Effective fix applied
Updated `~/.openclaw/openclaw.json`:

```json
"memory-lancedb": {
  "enabled": true,
  "config": {
    "embedding": {
      "apiKey": "ollama-local",
      "model": "mxbai-embed-large",
      "baseUrl": "http://192.168.79.1:11434/v1",
      "dimensions": 1024
    },
    "autoCapture": true,
    "autoRecall": true
  }
}
```

## Env interpolation check
The plugin config parser supports `${ENV_VAR}` expansion.
Verified from source: `resolveEnvVars()` in `extensions/memory-lancedb/config.ts`.

However, the effective running config was not using `${OPENAI_API_KEY}` here. The service config already used:
- `apiKey: "ollama-local"`

That is acceptable for local Ollama OpenAI-compatible endpoints.

## Net result
- env interpolation support: YES
- actual effective fix: service config baseUrl corrected to `/v1`
