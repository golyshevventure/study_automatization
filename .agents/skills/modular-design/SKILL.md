---
name: modular-design
description: Technology-agnostic guidance for modular system design in StudyCore. Covers bounded contexts, clear boundaries, composability, state isolation, explicit contracts, and split/merge criteria. Use when designing or reviewing module structure, package layout, cross-cutting dependencies, or architecture discussions. Do NOT use for executing full decomposition pipelines (use modular-decomposition) or phased roadmaps (use module-planning).
---

# Modular Design Principles

Principles for reasoning about structure and boundaries in the StudyCore codebase.

## Layered Mental Model

- **Composition roots** (apps, hosts): wire modules together; keep orchestration thin.
- **Modules / bounded contexts**: cohesive units of behavior and data ownership.
- **Shared kernels** (use sparingly): only stable, truly cross-cutting concepts.

Physical layout (mono repo, packages, libraries) is a **delivery choice**, not the definition of modularity.

## The Ten Principles

| # | Principle | Intent |
|---|-----------|--------|
| 1 | **Well-defined boundaries** | Small, stable public surface; everything else is internal. |
| 2 | **Composability** | Modules combine without special knowledge of internals. |
| 3 | **Independence** | No hidden shared mutable state; testable in isolation. |
| 4 | **Individual scale** | Resources tunable per module without rewriting others. |
| 5 | **Explicit communication** | Cross-module interaction uses documented contracts. |
| 6 | **Replaceability** | Dependencies expressed through interfaces or protocols. |
| 7 | **Deployment independence** | Modules don't assume shared process unless decided. |
| 8 | **State isolation** | Each module owns its persistent state and naming. |
| 9 | **Observability** | Each module diagnosable on its own: logs, metrics, traces. |
| 10 | **Fail independence** | Failures contained so one module's outage doesn't cascade. |

For detailed rules per principle, load `references/principles.md`.

## Typical Violations

1. **Colliding concepts** — same name for different things in different modules.
2. **Reach-through persistence** — one module reading another's tables without contract.
3. **Centralized data ownership** — single persistence layer for all modules.
4. **Logic at the edge** — business rules in HTTP handlers instead of domain code.
5. **Leaky exports** — repositories or internal types exposed as public API.
6. **Facades that aren't thin** — public entry points embedding policy instead of delegating.

## Creating a Bounded Context

Use when introducing a new cohesive area:

1. **Scope and language** — Name the context; list core nouns/verbs (ubiquitous language).
2. **Responsibilities** — What decisions happen only here? What is out of scope?
3. **State ownership** — Which facts are authoritative in this context?
4. **Public contract** — Operations/events other contexts may use.
5. **Integrations** — For each neighbor: sync call, async message, shared read model?
6. **Invariants and lifecycles** — What must always be true inside this boundary?
7. **Isolation check** — Can you test core behavior without unrelated contexts?

## When to Split or Merge

**Default:** fewer boundaries until real pain appears.

### Six-criteria test (favor split when several are true)

| # | Criterion | Question |
|---|-----------|----------|
| 1 | **Language** | Different vocabulary or conflicting definitions? |
| 2 | **Rate of change** | Parts change on different cadences? |
| 3 | **Scale / SLO** | Different throughput or latency needs? |
| 4 | **Team** | Different teams own different parts? |
| 5 | **Risk** | Can one part bring down the other? |
| 6 | **Tech** | Different technology constraints? |
