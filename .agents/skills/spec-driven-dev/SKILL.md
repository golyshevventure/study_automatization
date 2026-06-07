---
name: spec-driven-dev
description: Spec-Driven Development process for StudyCore. 4 adaptive phases (Specify → Design → Tasks → Execute) with auto-sizing by complexity. Creates atomic tasks with verification criteria, requirement traceability, and GitHub milestone/issue tracking. Use when starting new modules, planning features, implementing with verification, or tracking progress. Triggers on "plan module", "specify feature", "design", "implement", "validate", "quick fix", "create milestone". Do NOT use for pure code review or non-technical tasks.
---

# Spec-Driven Development

Plan and implement StudyCore modules with precision.

```
┌──────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐
│ SPECIFY  │ → │  DESIGN  │ → │  TASKS  │ → │ EXECUTE │
└──────────┘   └──────────┘   └─────────┘   └─────────┘
   required      optional*      optional*     required

* Auto-skipped when scope doesn't need it
```

## Auto-Sizing

| Scope | What | Specify | Design | Tasks | Execute |
|-------|------|---------|--------|-------|---------|
| **Small** | ≤3 files, one sentence | Quick mode — skip pipeline | — | — | Implement + verify |
| **Medium** | Clear feature, <10 tasks | Brief spec | Skip — inline | Skip — implicit | Implement + verify |
| **Large** | Multi-component feature | Full spec + IDs | Architecture | Full breakdown | Implement per task |
| **Complex** | Ambiguity, new domain | Full spec + discuss gray areas | Research + arch | Breakdown + parallel | Implement + interactive UAT |

**Rules:**
- **Specify and Execute are always required.**
- **Design is skipped** when no architectural decisions needed.
- **Tasks is skipped** when ≤3 obvious steps.
- **Safety valve:** Even when Tasks is skipped, Execute ALWAYS lists atomic steps inline. If >5 steps or complex deps, STOP and create formal tasks.

## Project Structure

```
docs/
├── [module-name]/
│   ├── SPEC.md           # Requirements with traceable IDs
│   ├── SPEC_PATCH_vX.Y.md # Patch specifications
│   ├── REPORT_STAGE_N.md  # Stage completion reports
│   ├── REPORT_PATCH_*.md  # Patch reports
│   └── REPORT_FINAL.md    # Module completion report
```

## Workflow

### Specify

1. Define user story and acceptance criteria.
2. Identify goals and non-goals.
3. List risks and constraints.
4. Create requirement IDs (REQ-001, REQ-002, ...).

Load `references/spec-template.md` for the StudyCore SPEC format.

### Design

1. Architecture overview (components, data flow).
2. Data models (DB schema, API contracts).
3. Technology decisions with rationale.
4. Diagrams (mermaid).

### Tasks

1. Break down into atomic tasks.
2. Define dependencies between tasks.
3. Assign verification criteria to each task.
4. Estimate effort.

### Execute

1. List atomic steps inline.
2. Implement with verification after each step.
3. Run tests.
4. Update progress.

## GitHub Integration

Load `references/github-workflow.md` for:
- Milestone creation and naming
- Issue creation with labels and acceptance criteria
- Issue closure with reports
- Progress tracking

## Context Loading Strategy

**Base load:**
- SPEC.md (when working on a feature)
- Latest REPORT_*.md (for context on what's done)

**On-demand:**
- Design docs (when implementing from design)
- GitHub workflow (when creating milestones/issues)

## Commands

| Trigger | Action |
|---------|--------|
| "Plan module X" | Create SPEC.md with 4 phases |
| "Create milestone" | GitHub milestone + issues |
| "Implement feature" | Execute from spec |
| "Quick fix" | Small scope, skip pipeline |
| "Validate work" | Verify against acceptance criteria |
