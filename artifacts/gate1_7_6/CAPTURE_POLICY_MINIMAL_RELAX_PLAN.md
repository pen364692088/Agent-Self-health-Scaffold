# CAPTURE_POLICY_MINIMAL_RELAX_PLAN

Date: 2026-03-10

## Diagnosis
No global policy relaxation is required yet.
The policy already accepts valid preference / instruction / profile-fact inputs.
The current blocker is that runtime is feeding recalled wrapper content into `shouldCapture()` instead of isolated raw user text.

## Preferred minimal fix
Do NOT loosen generic source guards first.
Instead, narrow the evaluated content source before `shouldCapture()`:

### Option A — preferred
Only pass raw user-authored message text blocks to autoCapture.
Do not pass merged prompt text containing injected recall wrapper.

### Option B
Before evaluating capture rules, strip any leading injected memory block:
- remove `<relevant-memories>...</relevant-memories>`
- then evaluate the remaining user message body

### Option C
If content source cannot be separated immediately, allow a very narrow unwrap rule:
- if text starts with `<relevant-memories>` and also contains a raw user message segment outside the wrapper,
  only evaluate the raw user segment

## Minimal relax plan if policy must be loosened
If a temporary policy relaxation is unavoidable, only relax for these categories:
- preference
- instruction

### safe narrow relax
Allow capture when:
- text contains `remember`
- and one of `prefer`, `always`, `want`, `need`, `like`, `hate`, `love`
- and text does not contain system/developer/tool execution phrases

### do not relax
Do not remove these guards globally:
- prompt injection patterns
- XML/system-content guard
- markdown-summary guard
- emoji-heavy guard

## Why
The current logs already show source contamination by recalled wrapper content.
If we broadly relax source guards, we risk capturing injected/system text instead of user facts.

## Recommendation
1. Fix source selection first
2. Re-run `AUTOCAPTURE-PROOF-001`
3. Only if still blocked, apply a narrow preference/instruction relax
