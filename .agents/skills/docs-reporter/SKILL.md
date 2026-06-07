---
name: docs-reporter
description: Write, review, and edit documentation and progress reports for the StudyCore project. Use when creating docs, reviewing markdown files, writing READMEs, updating `/docs` directories, writing REPORT_STAGE_N.md, REPORT_PATCH_*.md, or REPORT_FINAL.md. Covers technical documentation, spec files, and session reports. Do NOT use for code comments, inline JSDoc, or API reference generation.
---

# Docs Reporter

Produce and refine documentation and reports that are accurate, clear, consistent, and easy to understand.

## Step 1: Understand the Goal

1. **Clarify the request:** Identify the core feature, command, or concept that needs work.
2. **Differentiate:** Writing new content vs editing existing content.
3. **Formulate a plan:** Step-by-step plan for required changes.

## Step 2: Investigate

1. **Read the code:** Examine relevant codebase to ensure docs are backed by implementation.
2. **Identify files:** Locate specific documentation files that need modification.
3. **Check connections:** If you change behavior, check for other pages that reference it. Update links.

## Step 3: Write or Edit

1. **Follow the style guide:** Active voice, clear headings, consistent terminology.
2. Ensure docs accurately reflect the code.
3. Use tables for comparisons, mermaid for diagrams, checklists for progress.

## Step 4: Report Templates

### REPORT_STAGE_N.md

```markdown
# Stage N: [Name]

## Summary
What was implemented in this stage.

## Files Changed
| File | Change |
|------|--------|
| path/to/file | Description |

## Tests
- [ ] Unit tests written
- [ ] Unit tests passing
- [ ] Integration tests (if applicable)

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Blockers
None / [description]

## Next Steps
What follows from this stage.
```

### REPORT_PATCH_*.md

```markdown
# Patch: [Name] vX.Y

## Goal
What this patch addresses.

## Changes
- Change 1
- Change 2

## Regression Testing
- [ ] Existing features work
- [ ] No breaking changes

## Metrics
- Lines changed: N
- Tests added: N
```

### REPORT_FINAL.md

```markdown
# Final Report: [Module Name]

## Summary
Overall what was built.

## Stages Completed
| Stage | Status | Report |
|-------|--------|--------|
| 1 | ✅ | Link |

## Metrics
- Total files changed: N
- Total tests: N passing
- Coverage: X%

## Lessons Learned
- Lesson 1
- Lesson 2

## Next Steps
Future work.
```

## Step 5: Verify

1. Re-read files for formatting and correctness.
2. Verify all links in new content.
3. Ensure consistent terminology across all documents.
