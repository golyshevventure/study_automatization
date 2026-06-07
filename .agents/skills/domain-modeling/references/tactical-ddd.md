# Tactical DDD — Building Blocks

## Entity

Has unique identity tracked over time.

```python
# ✅ Entity
class DeadlineEvent:
    def __init__(self, id: str, title: str, event_date: date):
        self.id = id          # identity
        self.title = title
        self.event_date = event_date
```

## Value Object

No identity. Defined by attributes. Immutable.

```python
# ✅ Value Object
@dataclass(frozen=True)
class EventDate:
    date: date
    timezone: str = "Europe/Moscow"

    def is_past(self) -> bool:
        return self.date < date.today()
```

## Aggregate

Cluster of Entities and Value Objects with one root Entity.

```python
# ✅ Aggregate
class DeadlineAggregate:
    def __init__(self, root: DeadlineEvent):
        self.root = root          # Aggregate Root
        self.variants: list[DeadlineEvent] = []

    def add_variant(self, event: DeadlineEvent):
        if event.title == self.root.title:
            self.variants.append(event)
        else:
            raise ValueError("Variant must match aggregate title")
```

Rules:
- One transaction = one Aggregate.
- Reference other Aggregates by ID only.
- Protect invariants at the Aggregate boundary.

## Domain Service

Operation that doesn't belong to any Entity or Aggregate.

```python
# ✅ Domain Service
class DeadlineMerger:
    def merge(self, events: list[DeadlineEvent]) -> list[DeadlineAggregate]:
        # Business logic for grouping duplicates
        ...
```

Use sparingly. Excessive services → anemic model.

## Domain Event

Something that happened in the domain.

```python
# ✅ Domain Event
@dataclass
class SyncCompleted:
    user_id: str
    items_synced: int
    timestamp: datetime
```

Publish after successful state change. Use for cross-Aggregate communication.

## Refactoring Steps

1. **Replace setter chains** with a single expressive method.
2. **Move service logic** into the Aggregate that owns it.
3. **Add business guards** at the top of each method.
4. **Publish Domain Events** after each state change.
5. **Replace primitive types** with Value Objects.

## Golden Rules

1. **Behaviour with data** — Objects own both state and operations.
2. **Ubiquitous Language** — Method names come from domain (`commit_to_exam`, not `set_status`).
3. **Small Aggregates** — Root + VOs by default.
4. **One transaction = one Aggregate** — Cross-Aggregate rules use eventual consistency.
5. **Reference by ID** — Never hold object references to other Aggregates.
6. **Value Objects first** — Use Entities only when identity is essential.
7. **Domain Services sparingly** — Excessive services = anemic model.
8. **Protect invariants** — The Aggregate is the last line of defence.
