# Product Brief: ReleasePilot

**Version**: 0.1 (Draft)
**Status**: Proposal
**Last Updated**: 2026-03-09

---

## 1. User Persona

### Primary: Alex - Engineering Lead

- **Role**: Engineering Lead at a 50-person startup
- **Responsibility**: Oversees 6 development teams, each releasing weekly
- **Current Pain**: Spends 4+ hours per week reviewing/approving release notes
- **Tech Stack**: GitHub, GitHub Actions, Slack, Linear
- **Budget**: $50-200/month for developer productivity tools
- **Decision Power**: Can approve team-level SaaS purchases

### Secondary: Jordan - Solo Founder

- **Role**: Building a side project while working full-time
- **Current Pain**: No time for proper release documentation
- **Tech Stack**: GitHub, Vercel, Supabase
- **Budget**: Free or <$20/month
- **Decision Power**: Solo decision maker

---

## 2. User's Real Complaints (From Research)

> "Every release I spend 2 hours writing changelog and release notes. It's pure busywork."
> — Developer on Reddit

> "Our changelog is inconsistent. Some teams write good notes, others just say 'bug fixes'."
> — Engineering Manager

> "I pushed a breaking change without realizing. Had to hotfix at 2am."
> — Full-stack Developer

> "New team members have no idea what changed in the last 6 months."
> — Tech Lead

---

## 3. Current Alternatives & Why They Fail

| Alternative | Why It Doesn't Work |
|-------------|---------------------|
| Manual Writing | Time-consuming, inconsistent, often skipped |
| Conventional Commits | Requires team discipline, doesn't analyze actual code |
| Semantic Release | Good for versioning, bad for human-readable notes |
| ChatGPT | Generic output, not repo-contextual |
| Copy-paste from PRs | Fragmented, requires synthesis |

---

## 4. Minimum Decision Point

**The moment a user decides to use ReleasePilot:**

> "I just merged 15 PRs. I need to release in 30 minutes. I don't have time to write documentation."

**Alternative**: Spend 2 hours manually writing release notes.
**With ReleasePilot**: Run `releasepilot generate` → Get complete release package in 2 minutes.

---

## 5. Core Value Proposition

**"Turn git commits into production-ready release packages in 2 minutes."**

Key benefits:
- ⏱️ **Save 2+ hours per release**
- 📋 **Consistent documentation across teams**
- ⚠️ **Catch breaking changes before deployment**
- 📖 **Onboard new engineers faster with searchable release history**

---

## 6. Input / Output Specification

### Input
- Git repository URL or local path
- Version tag or commit range
- Optional: Project context (product description, target audience)

### Output: The "Release Package"

```
release-package/
├── CHANGELOG.md           # Semantic changelog
├── RELEASE_NOTES.md       # User-friendly announcement
├── DEPLOYMENT_CHECKLIST.md
├── RISK_ASSESSMENT.md
├── ROLLBACK_GUIDE.md
└── HANDOFF_SUMMARY.md
```

---

## 7. Minimum Feature Set (MVP)

### Must Have (P0)
- [ ] Git commit analysis
- [ ] Changelog generation (markdown)
- [ ] Release notes generation
- [ ] Basic risk flagging (breaking changes)
- [ ] CLI interface

### Should Have (P1)
- [ ] Deployment checklist generation
- [ ] Rollback guide generation
- [ ] GitHub integration (PR/issue linking)

### Nice to Have (P2)
- [ ] Slack integration
- [ ] Custom templates
- [ ] Multi-repo support

---

## 8. Non-Goals (Scope Boundaries)

❌ NOT building:
- Automated deployment execution
- CI/CD pipeline management
- Production monitoring
- Code review functionality
- Issue tracking

**Reasoning**: Focus on documentation output, not infrastructure control. Reduces scope and risk.

---

## 9. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| AI generates inaccurate release notes | Medium | High | Confidence scores + human review step |
| Users don't trust AI-generated docs | Medium | High | Allow edits before final output |
| GitHub API changes | Low | Medium | Abstract API layer, support local git |
| Competitors ship similar feature | Medium | Medium | Focus on quality, not just automation |

---

## 10. Tomorrow's Human Decision Points

1. **Pricing Model**: Usage-based vs seat-based?
2. **Delivery Format**: CLI-first vs Web UI first?
3. **Target Segment**: Team focus vs solo dev focus?
4. **Integration Priority**: GitHub vs GitLab vs both?

---

## 11. Success Metrics (Post-MVP)

| Metric | Target |
|--------|--------|
| Time saved per release | 1+ hour |
| User retention (30-day) | 60%+ |
| NPS | 40+ |
| Documentation completeness | 90%+ of releases have docs |

