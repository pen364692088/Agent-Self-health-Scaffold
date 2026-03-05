| Check | Result | Evidence |
|---|---|---|
| Install + Build (`npm ci` + `npm run build`) | PASS | `evidence/build.log` (build complete, 5 pages generated) |
| Link validation (`npx linkinator ./dist --recurse`) | PASS | `evidence/linkcheck.txt` (11 links scanned, all 200) |
| Live site HEAD (`/CVWebsite/`) | PASS | `evidence/online-check.txt` (HTTP/2 200) |
| Live PDF HEAD (`/CVWebsite/cv.pdf`) | PASS | `evidence/online-check.txt` (HTTP/2 200, `content-type: application/pdf`) |
| Responsive verification notes refreshed | PASS | `evidence/responsive-notes.md` updated |

Overall: PASS
