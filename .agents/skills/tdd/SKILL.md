---
name: tdd
description: Test-driven development with red-green-refactor loop for StudyCore. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development. Covers pytest for backend (FastAPI, SQLAlchemy) and Vitest for frontend (React). Do NOT use for adding tests to existing code without changes.
---

# Test-Driven Development

## Philosophy

**Core principle**: Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** exercise real code paths through public APIs. They describe _what_ the system does, not _how_. A good test reads like a specification — "user can sync deadlines and see them grouped by program." These tests survive refactors.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or query the database directly instead of using the interface. Warning sign: test breaks when you refactor, but behavior hasn't changed.

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.**

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```

Tests written in bulk test _imagined_ behavior, not _actual_ behavior. You outrun your headlights.

## Workflow

### 1. Planning

Before writing any code:

- [ ] Confirm with user what interface changes are needed
- [ ] Confirm which behaviors to test (prioritize)
- [ ] Design interfaces for testability
- [ ] List behaviors to test (not implementation steps)
- [ ] Get user approval on the plan

Ask: "What should the public interface look like? Which behaviors are most important to test?"

**You can't test everything.** Focus on critical paths and complex logic.

### 2. Tracer Bullet

Write ONE test that confirms ONE thing:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

This proves the path works end-to-end.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:
- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass:

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Backend Testing (pytest + FastAPI)

### Test Database

```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from backend.models.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_studycore"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db(engine):
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
```

### Testing Services

```python
# Test through public interface
async def test_sync_creates_events(db):
    service = DeadlineService(db)
    result = await service.sync(user_id="test")
    assert result.items_count > 0
    events = await service.list_events(user_id="test")
    assert len(events) > 0
```

### Testing API Endpoints

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_list_deadlines():
    response = client.get("/api/deadlines")
    assert response.status_code == 200
    assert "events" in response.json()
```

## Frontend Testing (Vitest + React)

```typescript
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Deadlines } from "./Deadlines"

const queryClient = new QueryClient()

test("shows loading state", () => {
  render(
    <QueryClientProvider client={queryClient}>
      <Deadlines />
    </QueryClientProvider>
  )
  expect(screen.getByText(/загрузка/i)).toBeInTheDocument()
})
```

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```
