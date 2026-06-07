---
name: studycore-architecture
description: StudyCore project architecture, technology stack, directory structure, and coding conventions. Use when implementing features, onboarding to the codebase, reviewing structure, or making architectural decisions. Covers FastAPI backend, React+TS+Vite frontend, PostgreSQL+SQLAlchemy 2.0 database, Alembic migrations, and project conventions. Do NOT use for Netology API specifics (use studycore-netology-api) or general coding principles (use coding-principles).
---

# StudyCore Architecture

StudyCore is a local automation platform for the Netology educational platform. It synchronizes schedule, deadlines, and materials, then processes them (transcription, summarization, conspect generation).

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI | latest |
| Backend DB | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.0.50 |
| Migrations | Alembic | latest |
| Validation | Pydantic | v2 |
| Frontend | React | 18+ |
| Frontend Build | Vite | 8 |
| Frontend Lang | TypeScript | strict |
| Styling | Tailwind CSS | latest |
| Icons | Lucide React | latest |
| State | React Query (TanStack Query) | latest |
| Python | CPython | 3.12 |

## Directory Structure

```
Study_automatization/
├── backend/                  # FastAPI application
│   ├── api/                  # Routers (deadlines, auth, etc.)
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # Business logic services
│   ├── dependencies/         # FastAPI dependency injection
│   └── alembic/              # Migration files
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── pages/            # Route-level pages
│   │   ├── components/       # Reusable UI components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── api/              # API client functions
│   │   └── types/            # TypeScript type definitions
│   └── package.json
├── docs/                     # Project documentation
│   └── DEDLINES_MODULE/      # Module-specific docs
├── tests/                    # Python tests (pytest)
├── src/                      # Legacy Python modules
│   ├── Генераторы/
│   ├── Скрейперы/
│   └── Хранилище/
├── Утилиты/                  # Utility scripts
├── Тесты/                    # Test/exploration scripts
├── Данные/                   # Local database + JSON dumps
└── data/                     # Runtime data (audio, HTML debug)
```

## Conventions

### Python (Backend)
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes.
- **Types:** Annotate everything. Use `str | None`, `list[int]` (Python 3.12).
- **Async:** All I/O is async. Endpoints are `async def`.
- **DB Models:** Use `Mapped[T]` + `mapped_column()`. Relationships use `lazy="selectin"`.
- **Services:** Injectable classes with `async def` methods. Business logic lives here, not in routers.

### TypeScript (Frontend)
- **Naming:** `camelCase` for functions/variables, `PascalCase` for components/types.
- **Strict:** `strict: true` in `tsconfig.json`. Avoid `any`.
- **Imports:** `@/*` maps to `./src/*` (configured in `tsconfig.app.json` and `vite.config.ts`).
- **Components:** Functional components only. Props typed with interfaces.
- **API Calls:** Use React Query (`useQuery`, `useMutation`, `useInfiniteQuery`).

### Database
- **Engine:** PostgreSQL 16, database `studycore`.
- **Tables:** `user_sessions`, `deadline_events`, `deadline_sync_log` (and growing).
- **Migrations:** Managed by Alembic. Always generate migration after model changes.
- **Async:** Use `create_async_engine` + `AsyncSession`.

## Path Aliases

```typescript
// tsconfig.app.json
"paths": { "@/*": ["./src/*"] }

// vite.config.ts
resolve: { alias: { "@": path.resolve(__dirname, "./src") } }
```

## Environment

Key variables in `.env`:
- `DATABASE_URL` — PostgreSQL connection string
- Netology credentials (for sync services)

## Running Locally

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev  # port 5174

# Database (Docker or local PostgreSQL)
# Ensure `studycore` database exists
```
