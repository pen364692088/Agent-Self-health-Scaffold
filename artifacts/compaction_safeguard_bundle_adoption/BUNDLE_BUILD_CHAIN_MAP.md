# BUNDLE BUILD CHAIN MAP

## Answers

1. **What generates `reply-C5LKjXcC.js`?**
   - OpenClaw build chain uses **`tsdown`**.
   - Trigger path from repo metadata: `pnpm build` -> `node scripts/tsdown-build.mjs` -> `tsdown.config.ts`.

2. **What is the bundle source entry?**
   - The packed bundle is generated from **OpenClaw `src/*`**, not from the nested installed `@mariozechner/pi-coding-agent/dist/core/*` file tree at runtime.
   - In the installed npm artifact, only built `dist/` is present; source/build scripts are trimmed from the published package.

3. **Why did `dist/core/compaction/compaction.js` changes not enter the live bundle?**
   - Because the live runtime path is the packed OpenClaw bundle `dist/reply-C5LKjXcC.js`.
   - Patching the nested standalone dist file changed a file on disk, but **not the actual loaded packed artifact**.

4. **Generation command / generation dir / publish dir**
   - generation command: `pnpm build` (repo metadata)
   - wrapper: `node scripts/tsdown-build.mjs`
   - generation dir: repo `dist/`
   - publish dir in live install: `~/.npm-global/lib/node_modules/openclaw/dist/`

5. **Physical path loaded by live process**
   - `~/.npm-global/lib/node_modules/openclaw/dist/reply-C5LKjXcC.js`

6. **Alternate artifact/caching findings**
   - Strongest finding was **prepacked live artifact mismatch**, not cache illusion.
   - No source/build files existed locally in the installed package to regenerate in place.
   - Therefore the minimal adoption point was direct replacement/patch of the loaded packed artifact.

7. **Smallest working adoption point**
   - **replace patched live bundle + restart gateway**
