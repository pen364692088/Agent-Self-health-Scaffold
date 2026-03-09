# LIVE RUNTIME ADOPTION

## Scope
Verify whether the live runtime is actually executing code that contains the `prepareCompaction` root-fix that throws `invalid_cut_point_empty_preparation`.

## Answers

1. **Where is the live process loading compaction code from?**
   - The live runtime path previously observed in production traces remains the packed bundle path: `dist/reply-C5LKjXcC.js`.
   - The currently installed standalone dist core file does contain the root-fix, but the loaded live bundle does not.

2. **Does the live execution path contain the patch symbols?**
   - `InvalidCutPointEmptyPreparationError`: **NO** in `reply-C5LKjXcC.js`
   - `code = invalid_cut_point_empty_preparation`: **NO** in `reply-C5LKjXcC.js`
   - Both are present in the standalone dist core file, which means patching happened there but was not adopted into the loaded bundle.

3. **Did the live loaded bundle/file hash change?**
   - Yes, the current `reply-C5LKjXcC.js` hash is different from the earlier recorded hash.
   - Earlier recorded hash: `c4178adc2cb92236d7e46d8cc437c60dcdec8fb03d96c479b51c60d9a85b0565`
   - Current hash: `fce78377296fe6971d6f1b6e0d691fcc5e894b91a1b59cb6aed46bd9521b88c8`
   - However, the current bundle **still does not contain** the root-fix symbols.

4. **Is the runtime path still `reply-C5LKjXcC.js`?**
   - **YES**, that remains the operative packed runtime path under `~/.npm-global/lib/node_modules/openclaw/dist/reply-C5LKjXcC.js`.

5. **If still bundle-based, was the bundle regenerated with the root-fix?**
   - **No evidence of a regenerated bundle containing the root-fix.**
   - The bundle hash changed, but symbol inspection proves the patched error class/code were not included.
   - So the bundle was replaced or rebuilt at some point, but not with the required patch content.

6. **Is there cache evidence preventing the patch from taking effect?**
   - There is **no need to assume node module cache/build cache/process cache** as the primary explanation.
   - The simpler explanation is stronger: the live loaded bundle file itself lacks the patch symbols.
   - If the runtime is executing `reply-C5LKjXcC.js` and that file does not contain the patch, then non-adoption is already proven at the artifact level.

## Layered verdict

### 1. Adoption
**FAILED**

### 2. Semantic correction
**NOT REACHED in live bundle path**

### 3. Functional restoration
**NOT OBSERVED**

## Bottom line
The root-fix exists in standalone dist files but is **not adopted by the live packed runtime path**. The live runtime remains bundle-driven and the bundle currently lacks `InvalidCutPointEmptyPreparationError` and `invalid_cut_point_empty_preparation`.
