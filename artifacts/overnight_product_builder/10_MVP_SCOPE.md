# MVP Scope: ReleasePilot v0.1

**Timeline**: 7 days
**Delivery Model**: CLI tool
**Core Value**: Generate release documentation from git commits

---

## MVP Feature Matrix

| Feature | Priority | Complexity | Included in MVP |
|---------|----------|------------|-----------------|
| Git commit parsing | P0 | Medium | ✅ Yes |
| Changelog generation | P0 | Medium | ✅ Yes |
| Release notes generation | P0 | Medium | ✅ Yes |
| Basic risk flagging | P0 | Low | ✅ Yes |
| CLI interface | P0 | Low | ✅ Yes |
| Deployment checklist | P1 | Low | ✅ Yes |
| Rollback guide | P1 | Low | ✅ Yes |
| GitHub PR linking | P1 | Medium | ⏳ Phase 2 |
| Slack integration | P2 | Medium | ⏳ Phase 2 |
| Custom templates | P2 | Low | ⏳ Phase 2 |
| Web UI | P2 | High | ⏳ Phase 3 |

---

## Technical Architecture (MVP)

```
┌─────────────────────────────────────────────┐
│                  CLI Entry                   │
│            $ releasepilot generate           │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              Git Analyzer                    │
│  - Parse commits in range                    │
│  - Extract file changes                      │
│  - Identify change types                     │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              AI Engine                       │
│  - Summarize changes                         │
│  - Categorize by type                        │
│  - Flag risks                                │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              Output Generator                │
│  - CHANGELOG.md                              │
│  - RELEASE_NOTES.md                          │
│  - DEPLOYMENT_CHECKLIST.md                   │
│  - RISK_ASSESSMENT.md                        │
└─────────────────────────────────────────────┘
```

---

## MVP File Structure

```
releasepilot/
├── README.md
├── package.json
├── src/
│   ├── index.ts              # CLI entry point
│   ├── analyzer/
│   │   ├── git.ts           # Git operations
│   │   └── parser.ts        # Commit parsing
│   ├── engine/
│   │   ├── summarizer.ts    # AI summarization
│   │   └── risk.ts          # Risk detection
│   └── output/
│       ├── changelog.ts     # Changelog generator
│       ├── release.ts       # Release notes generator
│       └── checklist.ts     # Deployment checklist
├── templates/
│   ├── changelog.hbs
│   ├── release.hbs
│   └── checklist.hbs
└── tests/
    ├── fixtures/
    └── *.test.ts
```

---

## MVP Command Interface

```bash
# Basic usage
releasepilot generate --from v1.0.0 --to v1.1.0

# With options
releasepilot generate \
  --from HEAD~10 \
  --output ./release-docs \
  --format markdown

# Preview without writing
releasepilot generate --dry-run
```

---

## MVP Output Example

### CHANGELOG.md
```markdown
## [1.1.0] - 2026-03-09

### Added
- User authentication with OAuth2 support
- Dark mode theme option

### Fixed
- Memory leak in image processing module
- Incorrect timezone handling in scheduler

### Changed
- Updated API rate limiting logic
```

### RELEASE_NOTES.md
```markdown
# Release v1.1.0

We're excited to announce version 1.1.0 with two major features...

## New Features
- **OAuth2 Authentication**: Sign in with Google or GitHub
- **Dark Mode**: Reduce eye strain during late-night sessions

## Bug Fixes
- Fixed memory issues when processing large images
- Corrected timezone display in scheduled tasks

## Breaking Changes
⚠️ API rate limiting has changed. See migration guide.
```

### DEPLOYMENT_CHECKLIST.md
```markdown
# Deployment Checklist v1.1.0

## Pre-Deployment
- [ ] Run database migrations
- [ ] Update OAuth redirect URLs
- [ ] Verify rate limit configuration

## Deployment
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production

## Post-Deployment
- [ ] Verify OAuth flows
- [ ] Check memory metrics
```

---

## MVP Dependencies

| Package | Purpose |
|---------|---------|
| simple-git | Git operations |
| commander | CLI framework |
| handlebars | Template engine |
| openai | AI summarization |
| marked | Markdown parsing |

---

## MVP Success Criteria

1. ✅ Can generate changelog from git commits
2. ✅ Can generate release notes with user-friendly language
3. ✅ Can flag breaking changes
4. ✅ CLI works on macOS and Linux
5. ✅ Documentation is complete and clear

---

## Out of MVP Scope

- Web UI
- GitHub App integration
- Slack notifications
- Custom templates
- Team management
- Billing/payments

