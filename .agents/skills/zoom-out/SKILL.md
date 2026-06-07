---
name: zoom-out
description: Zoom out and give broader context or a higher-level perspective on a section of the StudyCore codebase. Use when unfamiliar with an area of code, needing to understand how a module fits into the bigger picture, or before making architectural changes. Provides a map of relevant modules, callers, and data flow.
---

# Zoom Out

Give a higher-level perspective on an unfamiliar section of the StudyCore codebase.

## When to Use

- Before modifying code in an unfamiliar module
- When a bug spans multiple files and the root cause is unclear
- Before proposing architectural changes
- When onboarding to a new part of the codebase
- When a change feels like it might have unexpected side effects

## Output

Provide a structured overview:

```markdown
## Module Map: [Area]

### Entry Points
[How does code reach this area? API endpoints, event handlers, UI callbacks]

### Key Modules
| Module | Responsibility | Dependencies |
|--------|---------------|--------------|
| module1 | What it does | What it calls |

### Data Flow
[How data moves through this area — ASCII or mermaid diagram]

### Callers
[Who calls into this area? Upstream dependencies]

### Callees
[What does this area call? Downstream dependencies]

### Domain Concepts
[Key terms from this area and their meanings]

### Risks of Change
[What could break if this area is modified]
```

## Rules

1. **Use domain vocabulary** — "Deadline sync service", not "the deadline_service.py file"
2. **Show relationships** — don't just list files, show how they connect
3. **Highlight seams** — where can behaviour be changed without editing in place?
4. **Flag hidden coupling** — implicit dependencies that aren't obvious from imports
5. **Keep it concise** — 1-2 minutes of reading, not a dissertation
