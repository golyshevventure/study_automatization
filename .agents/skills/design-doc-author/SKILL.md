---
name: design-doc-author
description: Creates Technical Design Documents (TDD) and Specifications for StudyCore modules. Covers document structure, high-level vs implementation details, scope definition, risk assessment, and alternatives analysis. Use when writing a design doc, spec, architecture document, RFC, or before implementing significant technical changes. Do NOT use for README files, API docs, or general documentation (use docs-reporter).
---

# Design Doc Author

Creates TDDs that communicate architecture decisions, implementation plans, and risk assessments.

## High-Level vs Implementation

**CRITICAL:** TDDs document **architectural decisions and contracts**, NOT implementation code.

### ✅ Include (High-Level)

| Category | Include | Example |
|----------|---------|---------|
| API Contracts | Request/Response schemas | `POST /deadlines/sync` with JSON body |
| Data Schemas | Table structures, field types | `DeadlineEvent` table: id, title, event_date |
| Architecture | Components, data flow | "Frontend → API → Service → Netology API → Database" |
| Decisions | What technology, why chosen | "Use React Query for server state caching" |
| Diagrams | Sequence, architecture, flow | Mermaid diagrams |
| Strategies | Approach, not commands | "Upsert: delete old → fetch → merge → insert" |

### ❌ Avoid (Implementation Code)

| Category | Avoid | Why |
|----------|-------|-----|
| CLI Commands | `alembic upgrade head` | Tooling may change |
| Code Snippets | TypeScript implementation | Belongs in code, not docs |
| Framework specifics | `@Injectable()`, decorators | Document pattern, not syntax |
| File paths | `backend/services/deadline_service.py` | Implementation detail |

**Guideline:** Ask "Will this change with tooling?" If yes, keep it high-level.

## Document Structure

### Required Sections

```markdown
# [Module Name] — Technical Design

## Context
What problem are we solving? Why now?

## Goals
- Goal 1
- Goal 2

## Non-Goals
What is explicitly out of scope?

## Problem Statement
Current pain points and limitations.

## Scope
- In scope: ...
- Out of scope: ...

## Technical Solution
Architecture overview, components, data flow.

## Data Model
Tables/entities and their relationships.

## API Design
Endpoints, request/response schemas.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Risk 1 | High | High | Mitigation strategy |

## Implementation Plan
Phases, milestones, dependencies.

## Testing Strategy
Unit tests, integration tests, manual verification.

## Alternatives Considered
| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Option A | ... | ... | Rejected because ... |
| Option B | ... | ... | Selected |
```

## Project Size Adaptation

| Size | Depth | Sections |
|------|-------|----------|
| **Small** | ≤3 files, one sentence | Context + Goals + Solution (1 page) |
| **Medium** | Clear feature, <10 tasks | All required sections |
| **Large** | Multi-component, new domain | All sections + detailed diagrams |

## Risk Assessment

For each risk, define:
- **Likelihood:** High / Medium / Low
- **Impact:** High / Medium / Low
- **Mitigation:** Specific action to reduce risk

Example risks for StudyCore:
- Netology API changes → breaks sync
- Cookies expire → auth failures
- Database schema changes → migration complexity

## Alternatives Considered

Always document at least 2 options:

```markdown
## Alternatives

### Option A: [Name]
**Pros:** ...
**Cons:** ...

### Option B: [Name] (Selected)
**Pros:** ...
**Cons:** ...
**Why selected:** ...
```

## Validation Rules

Before finalizing:
- [ ] All sections required for project size are present
- [ ] No implementation code in the doc
- [ ] All diagrams use mermaid or ASCII
- [ ] Risks have mitigations
- [ ] Alternatives section has ≥2 options
- [ ] Goals are measurable
- [ ] Non-goals are explicit
