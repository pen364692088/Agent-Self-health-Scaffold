# SHOULD_CAPTURE_SAMPLE_MATRIX

Date: 2026-03-10

## Sample matrix

| Sample | Text | matched candidate types | matched_rules | rejected_by_length | rejected_by_source | rejected_by_similarity | rejected_by_importance | rejected_by_category | Result |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| preference | `Remember this: I prefer dark mode.` | preference/instruction | remember, prefer, `i prefer` | false | false | false | false | false | shouldCapture=true |
| instruction | `Remember this: I always want concise answers.` | preference/instruction | remember, always | false | false | false | false | false | shouldCapture=true |
| profile fact | `My email is moonlight@example.com` | profile/entity | email, `my ... is` | false | false | false | false | false | shouldCapture=true |
| normal chat | `How are you today?` | none | none | false | false | false | false | false | shouldCapture=false |
| duplicate-like injected wrapper | `<relevant-memories> ... Remember this: I prefer dark mode ... </relevant-memories>` | preference/instruction | remember, prefer, `i prefer` | false | true | false | false | false | shouldCapture=false |
| too short | `dark mode` | none | none | true | false | false | false | false | shouldCapture=false |
| proof token | `Remember this exactly: AUTOCAPTURE-PROOF-001` | none | remember | false | false | false | false | false | shouldCapture=true |

## Interpretation
There are valid positive samples.
So the policy is not globally over-strict.

The negative runtime cases are specifically failing because the text entering `shouldCapture()` is not the raw user seed. It is the injected wrapper content, which is intentionally rejected by source filtering.

## Minimal positive samples
The smallest proven positives at function level are:
- `Remember this: I prefer dark mode.`
- `Remember this: I always want concise answers.`
- `My email is moonlight@example.com`
- `Remember this exactly: AUTOCAPTURE-PROOF-001`
