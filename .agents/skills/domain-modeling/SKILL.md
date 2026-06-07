---
name: domain-modeling
description: Domain-Driven Design analysis for StudyCore. Maps business domains, identifies bounded contexts, classifies subdomains (Core/Supporting/Generic), and applies tactical DDD patterns (Entities, Value Objects, Aggregates, Domain Services, Domain Events). Use when analyzing domain boundaries, designing modules, reviewing domain models, or detecting anemic models. Do NOT use for general code review or non-domain code (DTOs, controllers, infrastructure).
---

# Domain Modeling

DDD analysis for the StudyCore educational automation platform.

## Subdomain Classification

### Core Domain
Competitive advantage, highest business value, complex logic.

- **Indicators:** Frequent changes, domain experts needed, complex rules
- **StudyCore examples:** Netology sync engine, deadline merging/grouping, data extraction

### Supporting Subdomain
Essential but not differentiating, business-specific.

- **Indicators:** Supports Core Domain, moderate complexity
- **StudyCore examples:** Auth/session management, UI display logic

### Generic Subdomain
Common functionality, could be outsourced.

- **Indicators:** Well-understood problem, standard functionality
- **StudyCore examples:** Logging, configuration, file storage

### Decision Tree

```
Is it a competitive advantage?
  YES → Core Domain
  NO → Does it require business-specific knowledge?
        YES → Supporting Subdomain
        NO → Generic Subdomain
```

## Bounded Context

An explicit linguistic boundary where domain terms have specific, unambiguous meanings.

- Inside boundary: all terms are unambiguous.
- Goal: align 1 subdomain to 1 bounded context.

### StudyCore Bounded Contexts

| Context | Language | Key Entities |
|---------|----------|--------------|
| Deadlines | "event", "sync", "deadline" | DeadlineEvent, DeadlineSyncLog |
| Auth | "session", "token", "user" | UserSession |
| Programs | "program", "discipline", "lesson" | Program, Discipline, Lesson |
| Materials | "conspect", "transcription", "summary" | Material, Transcription |

## Cohesion Analysis

### High Cohesion Indicators ✅
- Concepts share ubiquitous language
- Frequently used together
- Direct business relationships
- Changes to one affect others in group

### Low Cohesion Indicators ❌
- Different vocabularies mixed
- Rarely used together
- No direct business relationship
- Changes don't affect others

### Cohesion Score

```
Score = (
  Linguistic Cohesion (0-3) +
  Usage Cohesion (0-3) +
  Data Cohesion (0-2) +
  Change Cohesion (0-2)
) / 10

8-10: High ✅
5-7:  Medium ⚠️
0-4:  Low ❌
```

## Tactical DDD Building Blocks

Load `references/tactical-ddd.md` for detailed guidance.

### Quick Reference

| Has identity? | Has invariants? | Building Block |
|---------------|-----------------|----------------|
| Yes | — | Entity |
| No | — | Value Object |
| Yes (root) + children | Yes | Aggregate |
| Spans multiple Aggregates | — | Domain Service |

- Prefer Value Objects over Entities.
- Prefer small Aggregates over large ones.
- One transaction = one Aggregate.
- Reference other Aggregates by ID only.

## Anemia Detection

Quick signals of anemic domain models:

```
public setX() / public setY()        → behaviour should be encapsulated
service.doX(entity, ...)              → logic likely belongs in entity
entity.setA(); entity.setB(); ...     → setter chain = missing intent method
no domain methods beyond getters      → pure data bag
```

## Integration Patterns

- **Shared Kernel:** Shared model between contexts (use sparingly).
- **Customer/Supplier:** Downstream depends on upstream.
- **Conformist:** Downstream conforms to upstream model.
- **Anti-corruption Layer:** Translate between external and internal models.
