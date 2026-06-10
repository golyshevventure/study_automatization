# Модуль генерации конспектов — Technical Design

## Context

StudyCore уже синхронизирует расписание и дедлайны с Netology. Следующий шаг — помочь студентам быстро усваивать материал через AI-конспекты. Существующий локальный pipeline (Obsidian + Whisper) непригоден для MVP: требует локального Whisper, GPU, сложной структуры папок. Нужна облачная версия, интегрированная в Telegram Mini App.

## Goals

1. Позволить пользователю генерировать конспекты из вебинаров Netology в 3 клика.
2. Сделать генерацию фоновой — пользователь не блокируется.
3. Хранить конспекты в PostgreSQL с возможностью поиска и редактирования.
4. Минимизировать стоимость LLM-токенов через VTT + extractive preprocessing.
5. Визуализировать связи между конспектами через граф знаний.

## Non-Goals

- Не обрабатываем PDF/DOCX/PPTX.
- Не обрабатываем видео без VTT.
- Не используем локальные модели (Whisper, Ollama).
- Не делаем авто-генерацию всех материалов — только on-demand.
- Не делаем sharing между пользователями.

## Problem Statement

1. Студентам приходится пересматривать длинные вебинары для подготовки к экзаменам.
2. Ручное конспектирование занимает 2–3 часа на вебинар.
3. Существующий локальный pipeline не масштабируется и требует технических навыков.
4. LLM API дорогие при прямой обработке полных транскрипций.

## Scope

**In scope:**
- Backend: API для списка программ/модулей/вебинаров, генерации конспектов, поиска, фильтрации.
- Background job: извлечение VTT, extractive summarization, LLM generation.
- Frontend: Home widget, Conspects page, generation modal, conspect viewer/editor, knowledge graph.
- Database: tables for conspects, conspect jobs, raw VTT cache.

**Out of scope (MVP):**
- File processing pipeline.
- Local Whisper fallback.
- Batch generation.
- Collaborative features.

## Technical Solution

### High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend  │────▶│ FastAPI API  │────▶│  Netology API   │
│  (React/TS) │◀────│   (Backend)  │◀────│   Client        │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Background   │
                    │ Job Queue    │
                    │ (async + DB) │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ VTT Extract│  │ Extractive │  │  OpenRouter│
    │ (Kinescope)│  │ Summarizer │  │    LLM     │
    └────────────┘  └────────────┘  └────────────┘
```

### Data Flow (Generation)

1. User selects webinar in modal.
2. API creates `ConspectJob` record (status = `queued`).
3. API enqueues ARQ job (`generate_conspect_task`) in Redis.
4. ARQ worker picks up job and runs task:
   a. Fetch VTT from Kinescope (via regex on HTML) → `extracting`
   b. Clean VTT (remove timestamps, duplicates) → raw transcript
   c. Extractive summarization (BERT/LexRank) → compressed text
   d. Send to OpenRouter LLM with structured prompt → `generating`
   e. Parse Pydantic output, save to `Conspect` table → `ready`
   f. On failure → ARQ retry 3x with exponential backoff → `failed`
5. Frontend polls job status via `GET /api/conspects/jobs/{id}` (reads from DB).
5. On ready, conspect appears in list.

### Cost Optimization Strategy

| Step | Technology | Cost |
|------|-----------|------|
| Transcription | VTT from Kinescope HTML | $0 |
| Cleanup | Local Python regex | $0 |
| Compression | BERT-extractive-summarizer or LexRank | $0 |
| Final summary | OpenRouter deepseek-v3.2 or gemini-2.0-flash | ~$0.02–0.05 per conspect |

**Target:** ≤ $0.05 per 60-min webinar conspect.

## Data Model

### Tables

```sql
-- Programs/Modules cache (read-only mirror of Netology structure)
netology_programs
  - id (PK, Netology program_id)
  - title
  - type (profession | program)
  - user_id (FK)
  - synced_at

netology_modules
  - id (PK)
  - program_id (FK)
  - title
  - netology_program_id (sub-program id)

netology_lessons
  - id (PK)
  - module_id (FK)
  - title
  - netology_lesson_id

netology_lesson_items
  - id (PK)
  - lesson_id (FK)
  - title
  - type (video | webinar | ...)
  - video_url
  - has_vtt (bool, validated)
  - vtt_extracted_at

-- Conspects
conspects
  - id (PK, uuid)
  - user_id (FK)
  - lesson_item_id (FK)
  - program_id (FK, denormalized for filtering)
  - module_id (FK, denormalized)
  - title
  - topic
  - summary (markdown/text)
  - key_points (jsonb[])
  - definitions (jsonb[])
  - difficulty (int 1-10)
  - raw_vtt (text, optional)
  - compressed_text (text, optional)
  - is_edited (bool)
  - created_at
  - updated_at

conspect_jobs
  - id (PK, uuid)
  - user_id (FK)
  - lesson_item_id (FK)
  - status (queued | extracting | generating | ready | failed)
  - error_message (text, nullable)
  - retry_count (int)
  - started_at
  - completed_at
  - conspect_id (FK, nullable)
```

### Search Index

```sql
-- Full-text search on conspects.title + conspects.summary
CREATE INDEX idx_conspects_search ON conspects 
USING gin(to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(summary,'')));
```

## API Design

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/summary/programs` | Список программ пользователя |
| GET | `/api/summary/programs/{id}/modules` | Список модулей программы |
| GET | `/api/summary/modules/{id}/webinars` | Список вебинаров модуля (только с VTT) |
| POST | `/api/summary/conspects/generate` | Создать фоновую задачу генерации |
| GET | `/api/summary/conspects` | Список конспектов (с поиском и фильтрами) |
| GET | `/api/summary/conspects/{id}` | Получить один конспект |
| PATCH | `/api/summary/conspects/{id}` | Редактировать конспект |
| DELETE | `/api/summary/conspects/{id}` | Удалить конспект |
| GET | `/api/summary/conspects/jobs/{id}` | Статус фоновой задачи |
| GET | `/api/summary/conspects/recent` | 3 последних конспекта для Home |
| GET | `/api/summary/knowledge-graph` | Данные для графа знаний |

### Key Request/Response Schemas

**POST /api/summary/conspects/generate**
```json
{
  "lesson_item_id": 2872860
}
```

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

**GET /api/summary/conspects**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Вводная встреча...",
      "program": { "id": "...", "title": "..." },
      "module": { "id": "...", "title": "..." },
      "created_at": "2026-05-23T...",
      "is_edited": false
    }
  ],
  "total": 42
}
```

**GET /api/summary/conspects/{id}**
```json
{
  "id": "uuid",
  "title": "...",
  "topic": "...",
  "summary": "# ...",
  "key_points": ["...", "..."],
  "definitions": [{"term": "...", "definition": "..."}],
  "difficulty": 5,
  "raw_vtt_length": 15000,
  "created_at": "...",
  "updated_at": "..."
}
```

**PATCH /api/summary/conspects/{id}**
```json
{
  "summary": "# Отредактированный markdown...",
  "key_points": ["..."]
}
```

## Component Design

### Infrastructure

```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  db:
    image: postgres:16
    # ... existing config
  
  app:
    # ... existing config + REDIS_URL
  
  summary_worker:
    build: .
    command: python -m backend.workers.summary_worker
    env_file: .env
    depends_on: [redis, db]
```

### Backend Services

| Service | Responsibility |
|---------|---------------|
| `NetologyProgramService` | Fetch/sync programs, modules, lessons, items from Netology API |
| `VTTExtractionService` | Extract VTT from Kinescope HTML via regex |
| `TextCompressionService` | Extractive summarization (BERT/LexRank) |
| `LLMSummaryService` | Structured summary generation via OpenRouter |
| `ConspectJobService` | Orchestrate background generation, retries, status updates |
| `ConspectSearchService` | Full-text search + filters |
| `KnowledgeGraphService` | Build graph data for frontend |

### Frontend Components

| Component | Responsibility |
|-----------|---------------|
| `RecentConspectsWidget` | Home page block (3 recent or CTA) |
| `ConspectsPage` | Main page with list, search, filters, graph |
| `GenerateConspectModal` | Step-by-step program → module → webinar selection |
| `ConspectViewer` | Read conspect with structured sections |
| `ConspectEditor` | Edit conspect (rich text/markdown) |
| `KnowledgeGraph` | Obsidian-style graph visualization |
| `JobStatusToast` | Show background generation progress |

## Technology Decisions

| Decision | Selected | Rationale |
|----------|----------|-----------|
| Background jobs | ARQ + Redis | Type-safe async job queue, reliable retries, Redis as broker + result backend. Scales beyond single process. |
| Extractive summarization | `bert-extractive-summarizer` or `sumy` (LexRank) | Reduces input tokens by 60–80% before LLM. Free, local. |
| LLM provider | OpenRouter (deepseek-v3.2 / gemini-2.0-flash) | Cheap, API key already in `.env`. Provider pattern allows switching. |
| Structured output | Pydantic + prompt template | Validates output, enables typed frontend rendering. |
| Search | PostgreSQL full-text (`to_tsvector` Russian) | Built-in, no extra service. Good enough for 1000s of conspects. |
| Graph visualization | `react-force-graph-2d` or `d3-force` | Lightweight, Obsidian-like force-directed graph. |
| Editor | `react-markdown-editor-lite` or plain textarea + markdown preview | Simple, no heavy WYSIWYG. |

## Implementation Phases

### Phase 1: Foundation (API + DB)
- DB migrations: `netology_programs`, `netology_modules`, `netology_lessons`, `netology_lesson_items`, `conspects`, `conspect_jobs`.
- API endpoints: programs, modules, webinars list.
- VTT extraction service (reuse `extract_vtt_text` from `audio_extractor.py`).
- Tests: VTT extraction on real Kinescope URLs.

### Phase 2: One End-to-End Flow
- Background generation job.
- Extractive summarization integration.
- LLM summary service with Pydantic output.
- Frontend: modal + status polling.
- **Interactive UAT:** user generates 1 conspect, evaluates quality.

### Phase 3: Conspect Management
- Conspect list page with search and filters.
- Conspect viewer/editor.
- Recent conspects widget on Home.
- Tests: CRUD, search, filters.

### Phase 4: Knowledge Graph
- Graph data API.
- Frontend graph component.
- Polish UI/UX.

## Testing Strategy

| Type | Coverage |
|------|----------|
| Unit | VTT parsing, Pydantic output parsing, extractive summarization |
| Integration | Full generation flow with mocked LLM, DB state transitions |
| API | pytest + TestClient for all endpoints |
| E2E | Manual: generate real conspect from user's webinar, verify quality |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Kinescope HTML changes | Medium | High | Abstract `VTTExtractor` interface, monitor failures |
| LLM hallucinations in summary | High | Medium | Structured output + user editing + compression reduces noise |
| Long VTT exceeds LLM context | Medium | High | Extractive compression + chunking with refine strategy |
| Background task fails silently | Low | High | Retry 3x, status tracking, dead-letter log |

## Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| **A: Local Whisper + Ollama** | Privacy, no API cost | Requires GPU, slow, unscalable | Rejected |
| **B: OpenAI Whisper API** | High accuracy | $0.36/hour, unnecessary if VTT exists | Rejected |
| **C: VTT + extractive + OpenRouter (selected)** | Free transcription, cheap LLM, scalable | Depends on Kinescope HTML | Selected |
| **D: Celery + Redis for jobs** | Robust queue | Extra infrastructure | Rejected for MVP, keep async + DB polling |
