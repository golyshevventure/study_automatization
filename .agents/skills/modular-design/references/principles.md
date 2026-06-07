# Modular Design Principles — Detailed

## 1. Well-defined boundaries

A module has a small, stable public API. Everything else is internal implementation detail.

**Rules:**
- Export only what consumers need.
- Internal functions/classes prefixed with `_` (Python) or not exported (TS).
- Version the public contract when it changes.

**Example:**
```python
# ✅ Public surface is small
class DeadlineService:
    async def sync(self, user_id: str) -> SyncResult: ...  # public
    async def _fetch_netology(self, user_id: str): ...      # internal
```

## 2. Composability

Modules can be used alone or combined without special knowledge.

**Rules:**
- No hidden initialization requirements.
- Dependencies passed explicitly (constructor injection).
- Default configurations work out of the box.

## 3. Independence

No hidden shared mutable state across boundaries.

**Rules:**
- Each module manages its own state.
- No global variables for module-specific state.
- Test with fakes or test doubles at the edges.

## 4. Individual scale

Resources tunable per module.

**Rules:**
- Connection pools, timeouts, batch sizes configurable per module.
- Don't hardcode global limits that affect all modules.

## 5. Explicit communication

Cross-module interaction uses documented contracts.

**Rules:**
- APIs, events, or messages — never direct database access to another module's tables.
- Contracts are typed (Pydantic models, TypeScript interfaces).

## 6. Replaceability

Dependencies on other modules through interfaces.

**Rules:**
- Define protocols/abstract base classes for external dependencies.
- Mock implementations for testing.

```python
# ✅ Interface
class CalendarProvider(Protocol):
    async def fetch_events(self, user_id: str) -> list[Event]: ...

# Implementation can be NetologyCalendarProvider, MockCalendarProvider, etc.
```

## 7. Deployment independence

Modules don't assume shared process.

**Rules:**
- Communication through network/API calls, not direct function calls across modules.
- In monolith: still design as if they could be extracted.

## 8. State isolation

Each module owns its persistent state.

**Rules:**
- One module = one schema/namespace in DB.
- No foreign keys across module boundaries.
- Reference other modules by ID, not object reference.

## 9. Observability

Each module diagnosable independently.

**Rules:**
- Structured logging with module identifier.
- Metrics per module (sync duration, error rate).
- Health checks for critical modules.

## 10. Fail independence

Failures contained within the module.

**Rules:**
- Timeouts on external calls.
- Circuit breaker for failing dependencies.
- Graceful degradation: if sync fails, show cached data.
