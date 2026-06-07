---
name: improve-codebase-architecture
description: Find deepening opportunities in the StudyCore codebase. Surfaces architectural friction and proposes refactors that turn shallow modules into deep ones. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make the codebase more testable and AI-navigable. Do NOT use for adding new features or fixing specific bugs.
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones.

## Glossary

Use these terms consistently:

- **Module** — anything with an interface and an implementation (function, class, package).
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, config. Not just the type signature.
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place.

Key principles:

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

## Process

### 1. Explore

Walk the codebase. Don't follow rigid heuristics — explore organically and note friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but real bugs hide in how they're called (no locality)?
- Where do tightly-coupled modules leak across their seams?
- Which parts are untested, or hard to test through their current interface?

Apply the **deletion test** to anything suspected shallow.

### 2. Present candidates

Write a markdown report to `docs/architecture/ARCHITECTURE_REVIEW_YYYY-MM-DD.md`.

For each candidate, include:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — in terms of locality, leverage, and testability
- **Before / After** — ASCII or mermaid diagram showing the change
- **Recommendation strength** — `Strong` / `Worth exploring` / `Speculative`

End with a **Top recommendation** section: which candidate to tackle first and why.

Use StudyCore domain vocabulary: "Deadline module", "Auth context", "Sync service" — not "the FooBarHandler".

### 3. Decision

Once the user picks a candidate, walk the design tree:

- Constraints and dependencies
- Shape of the deepened module
- What sits behind the seam
- What tests survive

Record decisions:
- New concept not in domain vocabulary? Add it to docs.
- User rejects with a load-bearing reason? Document it so future reviews don't re-suggest.
