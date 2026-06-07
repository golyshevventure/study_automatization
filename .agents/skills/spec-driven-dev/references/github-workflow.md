# GitHub Workflow for StudyCore

## Milestones

### Naming

Format: `[Module Name] vX.Y` or `[Module Name] Patch vX.Y`

Examples:
- `Deadlines Module v1.0`
- `Deadlines Patch v1.2`

### Creation

```bash
gh milestone create --title "Deadlines Module v1.0" --due-date "2025-06-30" --description "Implementation of the deadlines synchronization module"
```

### Description Template

```markdown
## Goal
[One-line goal]

## Scope
[What's included]

## Non-Goals
[What's excluded]

## Success Criteria
- [ ] All issues closed
- [ ] All tests passing
- [ ] Documentation complete
```

## Issues

### Creation

One issue per implementation phase:

```bash
gh issue create --title "[Module] Phase N: [Name]" --label "backend,database" --milestone "Module v1.0"
```

### Issue Template

```markdown
## Phase N: [Name]

### Goal
[What this phase implements]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests written and passing

### Related Requirements
- REQ-001, REQ-002

### Estimated Effort
[Story points or time]

### Dependencies
- [ ] Previous phase complete
```

### Labels

| Label | Use For |
|-------|---------|
| `backend` | Backend API, services, models |
| `frontend` | React components, hooks, pages |
| `database` | Schema, migrations, queries |
| `tests` | Unit tests, integration tests |
| `docs` | Documentation, reports |
| `bug` | Bug fixes |
| `enhancement` | New features |
| `refactor` | Code refactoring |

### Closure

Before closing an issue:
1. All acceptance criteria must be met.
2. Tests must pass.
3. A report must be written and committed.
4. Code must be committed and pushed.

Close with a summary comment:

```markdown
## Completed ✅

### What was done
[Summary]

### Files changed
- `path/to/file1` — [change]
- `path/to/file2` — [change]

### Tests
- [x] Unit tests passing (N tests)
- [x] Integration tests passing

### Report
See REPORT_STAGE_N.md

### Commit
`abc1234`
```

## Reports

### Report Naming

| Report | File | When |
|--------|------|------|
| Stage | `REPORT_STAGE_N.md` | After closing each issue |
| Patch | `REPORT_PATCH_vX.Y.md` | After patch completion |
| Final | `REPORT_FINAL.md` | After milestone closure |

### Report Commit

Always commit reports separately from code:

```bash
git add docs/MODULE_NAME/REPORT_STAGE_N.md
git commit -m "docs: add Stage N report for [Module]"
```

## Pull Requests

If using PRs (optional for solo development):

```bash
gh pr create --title "feat: implement [feature]" --body "Closes #42"
```

### PR Template

```markdown
## What
[Description]

## Why
[Motivation]

## How to test
1. Step 1
2. Step 2

## Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
```
