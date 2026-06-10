# Модуль генерации конспектов — Tasks Breakdown

## Phase 1: Foundation (DB + API + VTT)

| # | Task | Dependencies | Verification |
|---|------|--------------|------------|
| 1.0 | Add `redis` and `arq` to `backend/requirements.txt`; install packages | — | `pip show redis arq` succeeds |
| 1.1 | Create Alembic migrations for `netology_programs`, `netology_modules`, `netology_lessons`, `netology_lesson_items`, `conspects`, `conspect_jobs` | 1.0 | `alembic upgrade head` succeeds, tables exist |
| 1.2 | Create SQLAlchemy models with relationships | 1.1 | Models pass `sqlalchemy-stubs` / mypy checks |
| 1.3 | Create Pydantic schemas for API request/response | 1.2 | Schemas validate sample JSON |
| 1.4 | Implement `NetologyProgramService.get_user_programs()` | — | Endpoint returns real programs from Netology API |
| 1.5 | Implement `NetologyProgramService.get_program_modules(program_id)` | 1.4 | Returns modules for selected program |
| 1.6 | Implement `NetologyProgramService.get_module_webinars(module_id)` | 1.5 | Returns only `video`/`webinar` items with VTT availability check |
| 1.7 | Implement `VTTExtractionService.extract_vtt(kinescope_url)` — refactor from `audio_extractor.py` | — | Successfully extracts VTT from 3 real Kinescope URLs, returns clean text |
| 1.8 | API endpoints: `GET /api/summary/programs`, `/programs/{id}/modules`, `/modules/{id}/webinars` | 1.4–1.7 | pytest tests pass |

## Phase 2: One End-to-End Generation Flow

| # | Task | Dependencies | Verification |
|---|------|--------------|------------|
| 2.1 | Implement `ConspectJobService.create_job(lesson_item_id)` | 1.2 | Creates `conspect_jobs` row with status `queued` |
| 2.2 | Implement ARQ worker (`backend/workers/summary_worker.py`) with retry logic and Redis connection | 2.1 | Worker starts, connects to Redis, executes test task |
| 2.2a | Add Redis service to `docker-compose.yaml` | 2.2 | `docker compose up redis` succeeds, reachable on 6379 |
| 2.2b | Add `summary_worker` service to `docker-compose.yaml` | 2.2a | `docker compose up summary_worker` starts and processes jobs |
| 2.3 | Integrate extractive summarization (`bert-extractive-summarizer` or `sumy`) | 1.7 | Reduces VTT text by ≥ 50% while preserving key info |
| 2.4 | Implement `LLMSummaryService.generate(conspect_job_id)` with Pydantic structured output | 2.3 | Returns valid `ConspectContent` Pydantic model |
| 2.5 | Implement LLM Provider Pattern (OpenRouter + fallback support) | 2.4 | Can switch model via config |
| 2.6 | Save generated conspect to `conspects` table, link to job | 2.4 | Job status becomes `ready`, `conspect_id` populated |
| 2.7 | API: `POST /api/summary/conspects/generate` enqueues ARQ job, `GET /api/summary/conspects/jobs/{id}` | 2.1–2.6 | E2E test: generate 1 conspect from real webinar |
| 2.8 | Frontend: `GenerateConspectModal` with stepper (program → module → webinar) | 2.7 | User can select and submit |
| 2.9 | Frontend: Job status polling + toast notification | 2.8 | Status updates from `queued` → `ready` |
| 2.10 | **Interactive UAT** — user generates 3 conspects, evaluates quality | 2.9 | Quality score ≥ 7/10 |

## Phase 3: Conspect Management

| # | Task | Dependencies | Verification |
|---|------|--------------|------------|
| 3.1 | Implement `ConspectSearchService` with PostgreSQL full-text search | 1.2 | Search returns relevant results for test queries |
| 3.2 | Implement filters by program/module | 1.2 | Filtered list updates correctly |
| 3.3 | API: `GET /api/summary/conspects` (with search + pagination + filters) | 3.1–3.2 | Tests pass |
| 3.4 | API: `GET /api/summary/conspects/{id}`, `PATCH`, `DELETE` | 3.3 | CRUD tests pass |
| 3.5 | API: `GET /api/summary/conspects/recent` | 3.3 | Returns max 3 recent conspects |
| 3.6 | Frontend: `ConspectsPage` with list, search bar, filter dropdowns | 3.3–3.5 | Matches Figma/brand style |
| 3.7 | Frontend: `ConspectViewer` with structured sections | 3.6 | Renders all Pydantic fields |
| 3.8 | Frontend: `ConspectEditor` with markdown editing | 3.7 | Edit → save → reload shows updated content |
| 3.9 | Frontend: `RecentConspectsWidget` for Home page | 3.5 | Shows 3 recent or empty CTA |

## Phase 4: Knowledge Graph

| # | Task | Dependencies | Verification |
|---|------|--------------|------------|
| 4.1 | Implement `KnowledgeGraphService.build_graph(user_id)` | 1.2, 3.4 | Returns nodes (programs/modules/conspects) and edges |
| 4.2 | API: `GET /api/summary/knowledge-graph` | 4.1 | Returns graph data |
| 4.3 | Frontend: `KnowledgeGraph` component using `react-force-graph-2d` | 4.2 | Renders interactive graph |
| 4.4 | Integrate graph into `ConspectsPage` | 4.3 | Toggle list/graph view |
| 4.5 | UI polish: loading states, empty states, error states | 3.6–4.4 | Design review pass |

## Phase 5: Testing & Hardening

| # | Task | Dependencies | Verification |
|---|------|--------------|------------|
| 5.1 | Unit tests: VTT extraction, Pydantic parsing, extractive summarization | 1.7, 2.3–2.4 | ≥ 80% coverage |
| 5.2 | Integration tests: full generation flow with mocked LLM | 2.7 | Passes |
| 5.3 | API tests for all endpoints with TestClient | All API tasks | Passes |
| 5.4 | Error handling: Kinescope 403, LLM timeout, invalid VTT | 1.7, 2.4 | Graceful degradation |
| 5.5 | Performance: measure generation time and cost for 3 sample webinars | 2.10 | ≤ $0.05 and ≤ 3 min per conspect |

## Effort Estimate

| Phase | Estimated Time | Critical Path |
|-------|---------------|---------------|
| Phase 1 | 5–7 hours | Yes |
| Phase 2 | 8–12 hours | Yes |
| Phase 3 | 6–8 hours | Yes |
| Phase 4 | 4–6 hours | No (can ship without graph) |
| Phase 5 | 4–6 hours | Yes |
| **Total** | **27–41 hours** | |

## Priority Order

**Critical path (MVP):** 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7 → 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 2.7 → 2.8 → 2.9 → 2.10 → 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 3.7 → 3.8 → 3.9 → 5.1 → 5.2 → 5.3 → 5.4 → 5.5

**Can be deferred:** 4.1–4.5 (Knowledge Graph)
