# LIVE BUNDLE SOURCE OF TRUTH

The runtime source of truth for this bug was the loaded packed artifact:

- `~/.npm-global/lib/node_modules/openclaw/dist/reply-C5LKjXcC.js`

Not the nested standalone file:

- `~/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/dist/core/compaction/compaction.js`

The nested file contained the root-fix earlier, but the live runtime still executed the packed bundle path. After direct bundle patching, the loaded artifact now contains:

- `InvalidCutPointEmptyPreparationError`
- `invalid_cut_point_empty_preparation`
- `session_before_compact_invalid_cut_point_empty_preparation`
