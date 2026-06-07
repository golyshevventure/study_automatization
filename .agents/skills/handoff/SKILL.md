---
name: handoff
description: Compact the current session into a handoff document so another agent can continue the work. Use when the user says "pause", "handoff", "save context", "I'll be back", or when a session is ending and needs to be continued later. Creates a markdown summary with current state, open tasks, blockers, and next steps.
---

# Handoff

Create a handoff document summarising the current session so a fresh agent can continue the work.

## When to Use

- User says "pause", "handoff", "save context", "I'll be back"
- Session is ending and work needs to continue later
- Switching from one agent instance to another
- Long-running task needs to be resumed

## Output Format

Save to `docs/handoffs/HANDOFF_YYYY-MM-DD.md` in the project repository.

```markdown
# Handoff: [Date] — [Topic]

## Session Summary
[2-3 sentences about what was done in this session]

## Current State
- **Branch:** [git branch]
- **Commit:** [latest commit hash]
- **Backend:** [running / stopped / port]
- **Frontend:** [running / stopped / port]
- **Database:** [status, last migration applied]

## Completed
- [x] Task 1
- [x] Task 2

## In Progress
- [ ] Task 3 — [current step, what remains]
- [ ] Task 4 — [current step, what remains]

## Blockers
- [Blocker 1] — [description, what is needed to resolve]

## Decisions Made
- Decision 1: [what was decided and why]

## Next Steps (Priority Order)
1. [Next action with context]
2. [Next action with context]

## Files Changed (This Session)
| File | Change |
|------|--------|
| path/to/file | Brief description |

## Open Questions
- [Question that needs user input]

## Suggested Skills for Next Session
- [skill-name] — [why]
```

## Rules

1. **Do not duplicate** content already in PRDs, specs, ADRs, issues, commits. Reference them by path instead.
2. **Redact sensitive info** — API keys, passwords, session cookies.
3. **Be specific** — "Fix the auth bug" is bad. "Fix JWT datetime serialization in `security.py:25` — needs `.timestamp()` instead of datetime object" is good.
4. **Include context** — what was tried, what failed, what worked.
5. **Git status** — always include current branch and latest commit.
