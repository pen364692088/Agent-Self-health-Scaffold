# bundle generation commands

## Upstream build chain
- `pnpm build`
- `node scripts/tsdown-build.mjs`
- `tsdown` with `tsdown.config.ts`

## Live redeploy path used in this run
Because the installed package lacked local source/build scripts, the live redeploy used the minimal artifact-level adoption path:
1. backup `reply-C5LKjXcC.js`
2. patch the exact loaded bundle in place
3. restart gateway
4. verify bundle hash and patch symbols
