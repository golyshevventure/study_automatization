---
name: modular-decomposition
description: Sequenced analysis pipeline for decomposing the StudyCore codebase into modules. Patterns: identify components, find duplication, flatten hierarchy, analyze coupling, group into domains. Use when analyzing codebase structure, finding duplicated logic, measuring coupling, or grouping components into modules. Do NOT use for phased roadmaps or prioritization (use module-planning after this analysis).
---

# Modular Decomposition

Patterns 1–5 analysis pipeline for understanding and restructuring the StudyCore codebase.

## Workflow

1. **Scope:** Confirm structural analysis (inventory → coupling → grouping), not roadmap authoring.
2. **Order:** Run patterns 1 → 2 → 3 → 4 → 5 in order. Don't skip unless user explicitly limits scope.
3. **Load references:** For each pattern, open `references/decomposition-patterns.md` at the matching section.
4. **Carry context:** Reuse outputs from earlier patterns in later ones.
5. **Deliver:** Actionable findings tied to evidence from the repository.

## Ordered Patterns

| Step | Pattern | Purpose |
|------|---------|---------|
| 1 | Identify and size components | Inventory of all modules, classes, functions |
| 2 | Common domain detection | Find duplicated logic across modules |
| 3 | Flattening / hierarchy | Remove unnecessary nesting, orphaned code |
| 4 | Coupling analysis | Measure dependencies between modules |
| 5 | Domain identification and grouping | Group components into domain-aligned modules |

## Pattern 6 — Planning

After Pattern 5, switch to **module-planning** for phased implementation order, milestones, and tracking.

## Quick Start

- **Full pipeline:** "Run modular decomposition on this repo"
- **Single step:** "Find duplicated logic across modules" (Pattern 2)
- **Coupling:** "Analyze coupling between our packages" (Pattern 4)
