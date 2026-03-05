# Session State - Active Working Memory

**Purpose:** Current task context, critical details, and ongoing work
**Updated:** Every session with important information
**Format:** Structured for quick scanning and WAL Protocol updates

---

## Current Task
**Status:** [ACTIVE/PAUSED/COMPLETED]
**Started:** [timestamp]
**Description:** [brief description of current work]

### Key Details
- [Critical information that must survive context loss]
- [Specific values, decisions, preferences]
- [Names, URLs, IDs, configurations]

### Next Actions
- [ ] [Next step 1]
- [ ] [Next step 2] 
- [ ] [Next step 3]

### blockers/risks
- [Any issues preventing progress]
- [Decisions needed from human]
- [External dependencies]

---

## Recent Decisions (WAL Log)
**Format:** [timestamp] Decision: [what was decided and why]

---

## Active Context
**Files being worked on:** [list of relevant files]
**Commands in progress:** [any running processes]
**Environment state:** [relevant system/app status]

---

## Notes for Self
[Reminders, patterns learned, things to remember]

---

*Remember: Update this BEFORE responding when you hear corrections, decisions, or specific details.*