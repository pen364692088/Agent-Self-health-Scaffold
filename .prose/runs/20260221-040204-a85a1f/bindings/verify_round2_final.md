# Round 2 Final Re-Verification (commit `0bcef2b`)

| Check | Result | Evidence | Notes |
|---|---|---|---|
| `npm ci && npm run build` | PASS | `evidence/build.log` | Build completed successfully; 5 Astro pages generated. |
| `npx linkinator ./dist --recurse` | FAIL | `evidence/linkcheck.txt` | 6 broken links reported (`dist/CVWebsite/...` paths unresolved in local scan). Exit code 1. |
| Live URLs (`/`, `/about/`, `/projects/`, `/resume/`, `/contact/`, `/cv.pdf`) | PASS | `evidence/online-check.txt` | All checked URLs returned HTTP 200; PDF served as `application/pdf`. |
| Responsive notes refresh | PASS | `evidence/responsive-notes.md` | Notes updated with this verification pass timestamp and scope. |

Overall: FAIL
