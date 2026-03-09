# Opportunity Scorecard

**Scoring Criteria** (1-5 scale each):
1. **Pain Intensity** - How painful is the problem?
2. **Payment Willingness** - Will users pay to solve it?
3. **Delivery Capability** - Can we build it?
4. **Acquisition Ease** - How easy to reach customers?
5. **Automation Potential** - Can it be delivered automatically?

**Total Score** = Sum of 5 dimensions (max 25)

---

## Candidate Problems by Track

### Track A: Developer / R&D Delivery

| # | Problem | Pain | Pay | Capability | Acquisition | Auto | Total |
|---|---------|------|-----|------------|-------------|------|-------|
| A1 | Release notes generation | 5 | 4 | 5 | 5 | 5 | **24** |
| A2 | Breaking change detection | 5 | 4 | 4 | 4 | 4 | **21** |
| A3 | CI/CD pipeline optimization | 4 | 3 | 3 | 4 | 3 | **17** |
| A4 | Developer onboarding docs | 4 | 3 | 4 | 4 | 4 | **19** |
| A5 | Security vulnerability scanning | 5 | 4 | 3 | 3 | 3 | **18** |
| A6 | Changelog automation | 4 | 3 | 5 | 5 | 5 | **22** |
| A7 | Deployment checklist generation | 4 | 4 | 5 | 5 | 5 | **23** |
| A8 | Rollback recommendation | 5 | 4 | 4 | 4 | 4 | **21** |

### Track B: Academic Research

| # | Problem | Pain | Pay | Capability | Acquisition | Auto | Total |
|---|---------|------|-----|------------|-------------|------|-------|
| B1 | Literature synthesis | 5 | 2 | 4 | 3 | 3 | **17** |
| B2 | Citation formatting | 3 | 2 | 5 | 4 | 5 | **19** |
| B3 | Paper structure planning | 4 | 2 | 4 | 3 | 4 | **17** |
| B4 | Research data organization | 4 | 2 | 3 | 3 | 3 | **15** |
| B5 | Academic editing | 4 | 3 | 4 | 4 | 4 | **19** |

### Track C: Student Applications

| # | Problem | Pain | Pay | Capability | Acquisition | Auto | Total |
|---|---------|------|-----|------------|-------------|------|-------|
| C1 | Application deadline tracking | 4 | 2 | 4 | 4 | 4 | **18** |
| C2 | Essay feedback & editing | 5 | 3 | 4 | 4 | 3 | **19** |
| C3 | School requirement matching | 4 | 2 | 4 | 4 | 4 | **18** |
| C4 | Interview preparation | 4 | 3 | 3 | 3 | 2 | **15** |
| C5 | Application strategy | 5 | 3 | 3 | 3 | 2 | **16** |

---

## Top 3 Selection

| Rank | Problem | Score | Track | Rationale |
|------|---------|-------|-------|-----------|
| **#1** | A1: Release Notes Generation | 24 | Developer | Highest score; clear B2B payment willingness |
| **#2** | A7: Deployment Checklist Generation | 23 | Developer | High automation potential; complements A1 |
| **#3** | A6: Changelog Automation | 22 | Developer | Natural pair with A1; proven demand |

---

## Recommended Direction: A1 + A6 + A7 Combined

**Product Concept**: "ReleasePilot" - An AI agent that:
1. Analyzes git commits, PRs, and code changes
2. Generates release notes, changelog, and deployment checklists
3. Identifies potential breaking changes and risks
4. Produces handoff documentation for each release

**Why This Combination**:
- All three are high-scoring (24, 23, 22)
- Natural workflow: changelog → release notes → deployment
- Clear deliverable: "Release Package" with multiple outputs
- Strong B2B payment willingness
- GitHub-native (easy acquisition)
- High automation potential (entirely software-deliverable)

---

## Tie-Breaking Rules Applied

When scores are equal, priority order:
1. ✅ Developer tools (Track A > B > C)
2. ✅ Can output fixed result package
3. ✅ MVP achievable in 7 days
4. ✅ GitHub / issue / PR / docs workflow
5. ✅ Easy to demo

**Result**: All Top 3 are from Track A (Developer), satisfying tie-breaking rules.

---

## Uncertainty Notes

1. **Payment validation pending**: Need to verify actual willingness to pay for release automation
2. **Competitive landscape**: Semantic Release, Release Please exist but lack AI intelligence
3. **Integration complexity**: GitHub Actions vs standalone CLI decision needed

**Tomorrow's human decision required**: Confirm Track A focus before MVP build.
