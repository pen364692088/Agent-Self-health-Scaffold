# Round 3 Verification (repair run)

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Install + Build (`npm ci` + `npm run build`) | PASS | `/home/moonlight/Project/Github/MyProject/PersonWebsite/CVWebsite/evidence/build.log` | Build completed successfully; Astro reports 5 pages generated. |
| Link validation (`npx linkinator ./dist --recurse`) | FAIL | `/home/moonlight/Project/Github/MyProject/PersonWebsite/CVWebsite/evidence/linkcheck.txt` | 6 broken links reported under `dist/CVWebsite/...` during local scan. |
| Online URL checks (`/`, `/about/`, `/projects/`, `/resume/`, `/contact/`, `/cv.pdf`) | PASS | `/home/moonlight/Project/Github/MyProject/PersonWebsite/CVWebsite/evidence/online-check.txt` | All endpoints returned HTTP 200; PDF served with `content-type: application/pdf`. |

Overall: FAIL
