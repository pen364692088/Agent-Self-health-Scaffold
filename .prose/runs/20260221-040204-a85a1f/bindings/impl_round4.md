# Round 4 implementation note (linkcheck/base-path consistency)

## What changed
- Added `scripts/linkcheck-local.sh` to make local link verification base-path-aware for Astro `base: '/CVWebsite/'`.
  - Creates a temporary docroot `.tmp-linkcheck-root/CVWebsite/` from `dist/`.
  - Serves it locally via `python3 -m http.server`.
  - Runs `linkinator` against `http://127.0.0.1:4173/CVWebsite/` so `/CVWebsite/...` links resolve exactly as on GitHub Pages.
  - Cleans up temp files and server process with `trap`.
- Updated `package.json` scripts:
  - `linkcheck:local` -> `./scripts/linkcheck-local.sh`
  - `verify:local` -> `npm run build && npm run linkcheck:local`
- Updated README link-check section to use `npm run verify:local` and document why.

## Commands run
```bash
# from repo root
npm run build > /home/moonlight/.openclaw/workspace/.prose/runs/20260221-040204-a85a1f/evidence/build.log 2>&1
npm run linkcheck:local > /home/moonlight/.openclaw/workspace/.prose/runs/20260221-040204-a85a1f/evidence/linkcheck.txt 2>&1

{
  for url in \
    https://pen364692088.github.io/CVWebsite/ \
    https://pen364692088.github.io/CVWebsite/about/ \
    https://pen364692088.github.io/CVWebsite/projects/ \
    https://pen364692088.github.io/CVWebsite/resume/ \
    https://pen364692088.github.io/CVWebsite/contact/ \
    https://pen364692088.github.io/CVWebsite/cv.pdf
  do
    echo "\n## $url"
    curl -sS -o /dev/null -w "HTTP %{http_code}\nFinal %{url_effective}\n" -L "$url"
  done
} > /home/moonlight/.openclaw/workspace/.prose/runs/20260221-040204-a85a1f/evidence/online-check.txt
```

## Commit evidence
- Round 4 implementation commit: `16284279d1eca3783ab42f95a95b1fedba88204b`
- Repo: `/home/moonlight/Project/Github/MyProject/PersonWebsite/CVWebsite`

## Resulting status
- Local build completed successfully.
- Local link check passed with no broken links under base path behavior.
- Live URL checks returned HTTP 200 for all listed pages/assets.
