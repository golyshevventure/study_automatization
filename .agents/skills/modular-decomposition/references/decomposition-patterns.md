# Decomposition Patterns 1–5

## Pattern 1: Identify and Size Components

### Goal
Create an inventory of all structural units in the codebase.

### Steps
1. List all directories and files by layer (backend, frontend, utilities, tests).
2. For each module/service: count lines of code, number of public functions/classes.
3. Identify "oversized" components (>500 LOC or >10 public methods).
4. Flag components with mixed responsibilities.

### Output
```markdown
## Component Inventory

| Component | LOC | Public API | Responsibility | Size Rating |
|-----------|-----|------------|----------------|-------------|
| deadline_service.py | 320 | 8 | Sync + CRUD | Medium |
| netology_auth.py | 150 | 5 | Auth only | Small |
```

## Pattern 2: Common Domain Detection

### Goal
Find duplicated domain logic across modules.

### Steps
1. Search for similar function names, data structures, or business rules.
2. Compare implementations: same input/output but different code?
3. Check for "copy-paste" code blocks (>10 similar lines).
4. Identify shared concepts that should be in a shared kernel.

### Signals
- Same DTO/Model defined in multiple places
- Same validation logic in multiple endpoints
- Same business rule expressed differently

### Output
```markdown
## Duplication Findings

| Concept | Locations | Recommendation |
|---------|-----------|----------------|
| Date parsing | 3 files | Extract to `utils/date_parser.py` |
```

## Pattern 3: Flattening / Hierarchy

### Goal
Remove unnecessary nesting and orphaned code.

### Steps
1. Identify deeply nested directories (>3 levels without clear purpose).
2. Find orphaned classes/functions (not imported anywhere).
3. Check for "helper" files that became dumping grounds.
4. Ensure each file has a single, clear responsibility.

### Rules
- Flatten if nesting doesn't add clarity.
- Delete truly unused code (confirm with grep).
- Move misplaced code to correct module.

## Pattern 4: Coupling Analysis

### Goal
Measure dependencies between modules.

### Steps
1. Map imports: which modules import which.
2. Identify circular dependencies (A → B → A).
3. Measure fan-in (who depends on this) and fan-out (what this depends on).
4. Flag modules with high fan-in AND high fan-out (unstable).

### Metrics
```
Coupling Score = fan-out / total_modules

High coupling: >0.5
Medium coupling: 0.2–0.5
Low coupling: <0.2
```

### Output
```markdown
## Coupling Matrix

| Module | Fan-in | Fan-out | Score | Risk |
|--------|--------|---------|-------|------|
| auth | 5 | 2 | 0.3 | Medium |
| deadlines | 2 | 4 | 0.4 | Medium |
```

## Pattern 5: Domain Identification and Grouping

### Goal
Group components into domain-aligned modules.

### Steps
1. List business concepts (ubiquitous language).
2. Group components by concept they primarily serve.
3. Ensure each group has clear boundaries and single responsibility.
4. Validate: can each group be explained in one sentence?

### Grouping Criteria
- **Language:** Same vocabulary
- **Data:** Operates on same entities
- **Changes:** Modified together
- **Lifecycle:** Same creation/deletion patterns

### Output
```markdown
## Domain Groups

| Domain | Components | Responsibility |
|--------|------------|----------------|
| Deadlines | deadline_service, deadlines_router, DeadlineEvent | Sync and display deadlines |
| Auth | netology_auth, auth_middleware, UserSession | Authentication and sessions |
```
