---
name: coding-principles
description: Behavioral guidelines and language-specific conventions for writing, modifying, and reviewing code in the StudyCore project. Covers Python (FastAPI, SQLAlchemy 2.0, Pydantic v2, async) and TypeScript (React 18+, strict mode, hooks). Use when implementing features, refactoring, bug fixes, code review, or any code changes. Do NOT use for architecture design, documentation, or non-code tasks.
---

# Coding Principles

Behavioral guidelines to reduce common LLM coding mistakes. These principles bias toward caution over speed — for trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- Disagree honestly. If the user's approach seems wrong, say so.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

**The test:** Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

## 5. Python Conventions

### Type Hints
- Use type hints everywhere. Python 3.12 features: `str | None`, `list[int]`.
- Annotate return types on all functions, including `async def`.

### Async / Await
- All I/O operations must be async: database, HTTP, file system.
- Use `asyncio.gather()` for parallel I/O, not sequential `await`.
- Never mix sync and async code in the same call stack.

### SQLAlchemy 2.0
- Use `select()` with `async_session`.
- Prefer `.scalar()` / `.scalars().all()` over `.first()` / `.all()`.
- Use `Mapped[T]` and `mapped_column()` in models.
- Relationships: `lazy="selectin"` for async to avoid implicit lazy loads.

### Pydantic v2
- Use `BaseModel` for all data schemas.
- Validation: `model_validator(mode="after")`, not root validators.
- Serialization: `model_dump()` (not `.dict()`), `model_dump_json()`.

### FastAPI
- All endpoints: `async def`.
- Dependency injection for DB sessions, auth, services.
- Return typed Pydantic models, not raw dicts.

## 6. TypeScript / React Conventions

### Strict TypeScript
- `strict: true` in `tsconfig.json`. No `any` without explicit justification.
- Use `interface` for object shapes, `type` for unions and complex types.
- Prefer `unknown` over `any` for catch clauses.

### React
- Functional components only. No class components.
- Hooks rules: call at top level, never inside loops/conditions.
- `useEffect` must have cleanup for subscriptions, listeners, intervals.
- `useCallback` for functions passed to child components or `useEffect` deps.
- `useMemo` for expensive computations, not for every array map.

### Async in React
- Use `async/await` in event handlers, not in `useEffect` directly.
- In `useEffect`: define async function inside, call it immediately.
- Cancel pending requests on unmount with `AbortController`.
