# Phase 2 — Architecture Approval Request

## Scope

Один end-to-end flow: пользователь выбирает вебинар → система извлекает VTT → генерирует конспект через LLM → сохраняет в БД → пользователь видит результат.

## Services Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI App (main process)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │ SummaryRouter    │  │ NetologyProgram  │  │ ConspectJobService       │   │
│  │  (endpoints)     │◀─│ Service          │◀─│  (orchestration)         │   │
│  └────────┬─────────┘  └──────────────────┘  └────────────┬─────────────┘   │
│           │                                                │                 │
│           ▼                                                ▼                 │
│  ┌──────────────────┐                           ┌──────────────────────┐    │
│  │ VTTExtraction    │                           │ ARQ Redis Queue      │    │
│  │ Service          │                           │  (enqueue job)       │    │
│  └──────────────────┘                           └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARQ Worker (separate process)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │ generate_conspect│─▶│ VTTExtraction    │─▶│ TextCompressionService   │   │
│  │ _task            │  │ Service          │  │  (sumy / LexRank)        │   │
│  └──────────────────┘  └──────────────────┘  └────────────┬─────────────┘   │
│                                                           │                 │
│                                                           ▼                 │
│                                              ┌──────────────────────────┐   │
│                                              │ LLMSummaryService        │   │
│                                              │  (OpenRouter deepseek)   │   │
│                                              └────────────┬─────────────┘   │
│                                                           │                 │
│                                                           ▼                 │
│                                              ┌──────────────────────────┐   │
│                                              │ PostgreSQL: conspects,   │   │
│                                              │ conspect_jobs            │   │
│                                              └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Service Contracts

### 1. NetologyProgramService

```python
class NetologyProgramService:
    async def sync_user_programs(self, user_id: UUID, cookies: dict) -> list[NetologyProgram]:
        """Fetch programs from Netology API, upsert into netology_programs."""
        
    async def sync_program_modules(self, program_id: UUID, cookies: dict) -> list[NetologyModule]:
        """Fetch modules for program, upsert into netology_modules."""
        
    async def sync_module_lessons(self, module_id: UUID, cookies: dict) -> list[NetologyLesson]:
        """Fetch lessons for module, upsert into netology_lessons."""
        
    async def sync_lesson_items(self, lesson_id: UUID, cookies: dict) -> list[NetologyLessonItem]:
        """Fetch items for lesson, upsert into netology_lesson_items."""
        
    async def get_user_programs(self, user_id: UUID) -> list[ProgramResponse]:
        """Return cached programs from DB."""
        
    async def get_program_modules(self, program_id: UUID) -> list[ModuleResponse]:
        """Return cached modules from DB."""
        
    async def get_module_webinars(self, module_id: UUID) -> list[LessonItemResponse]:
        """Return video/webinar items with has_vtt=True from DB."""
```

### 2. VTTExtractionService

```python
class VTTExtractionService:
    async def extract_vtt(self, kinescope_url: str) -> str:
        """
        1. Fetch Kinescope embed HTML
        2. Extract playerOptions JSON via regex
        3. Find .vtt URLs in playerOptions
        4. Fetch VTT content
        5. Parse and clean (remove timestamps, duplicates)
        Returns: clean transcript text or "" on failure.
        """
        
    @staticmethod
    def _parse_vtt(vtt_content: str) -> str:
        """Remove WEBVTT headers, timestamps, cue numbers. Deduplicate lines."""
```

### 3. TextCompressionService

```python
class TextCompressionService:
    def compress(self, text: str, target_ratio: float = 0.3) -> str:
        """
        Extractive summarization using sumy (LexRank).
        Reduces text to ~30% of original while preserving key sentences.
        
        Args:
            text: Clean VTT transcript
            target_ratio: Target compression ratio (0.3 = 30% of original)
            
        Returns:
            Compressed text string
        """
```

### 4. LLMSummaryService

```python
class LLMProvider(Protocol):
    """Provider pattern for LLM APIs."""
    async def generate(self, prompt: str, schema: type[T]) -> T: ...

class OpenRouterProvider:
    """OpenRouter implementation. Uses deepseek-v3.2 by default."""
    DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324"
    
    async def generate(self, prompt: str, schema: type[T]) -> T:
        # 1. Call OpenRouter chat completions API
        # 2. Extract JSON from response
        # 3. Parse with Pydantic schema
        # 4. Return validated object

class LLMSummaryService:
    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or OpenRouterProvider()
        
    async def generate_conspect(self, compressed_text: str, title: str) -> ConspectContent:
        """
        1. Build prompt with system instructions + compressed_text + title
        2. Call LLM provider with ConspectContent schema
        3. Return structured conspect
        """

class ConspectContent(BaseModel):
    """Structured output from LLM."""
    topic: str
    summary: str
    key_points: list[str]
    definitions: list[dict[str, str]]  # [{"term": "...", "definition": "..."}]
    difficulty: int  # 1-10
```

### 5. ConspectJobService

```python
class ConspectJobService:
    async def create_job(
        self, 
        user_id: UUID, 
        lesson_item_id: UUID,
        db: AsyncSession
    ) -> ConspectJob:
        """
        1. Create ConspectJob row (status='queued')
        2. Enqueue ARQ task
        3. Return job record
        """
        
    async def update_status(
        self,
        job_id: UUID,
        status: str,
        db: AsyncSession,
        error_message: str = None,
        conspect_id: UUID = None,
    ) -> None:
        """Update job status in DB. Called by worker."""
```

## ARQ Worker Design

```python
# backend/workers/summary_worker.py

from arq import create_pool
from arq.connections import RedisSettings

redis_settings = RedisSettings(host="localhost", port=6379)

async def generate_conspect_task(ctx, job_id: str, user_id: str, lesson_item_id: str):
    """
    ARQ background task. Executed by worker process.
    
    Flow:
    1. Update status -> 'extracting'
    2. Fetch lesson_item from DB (get video_url)
    3. Extract VTT -> clean text
    4. Compress text (sumy LexRank)
    5. Update status -> 'generating'
    6. Call LLM -> structured ConspectContent
    7. Save to conspects table
    8. Update job -> 'ready', link conspect_id
    9. On any exception -> retry 3x, then 'failed'
    """
    
class WorkerSettings:
    functions = [generate_conspect_task]
    redis_settings = redis_settings
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    max_tries = 3
    retry_delay = 10  # seconds
```

**Retry strategy:**
- ARQ `max_tries=3` with exponential backoff (10s, 20s, 40s)
- On final failure: status → `failed`, error_message logged
- No dead-letter queue for MVP (just DB status + logs)

## Data Flow (Detailed)

```
User clicks "Сгенерировать конспект"
    │
    ▼
POST /api/summary/conspects/generate
    │
    ├──▶ ConspectJobService.create_job()
    │       ├──▶ INSERT INTO conspect_jobs (status='queued')
    │       └──▶ ARQ enqueue(generate_conspect_task, job_id, ...)
    │
    └──▶ Return { job_id, status: 'queued' }  (202 Accepted)
    │
    ▼
Frontend polls GET /api/summary/jobs/{job_id} every 2s
    │
    ▼
ARQ Worker picks up job:
    │
    ├──▶ status = 'extracting'
    │       ├──▶ SELECT video_url FROM netology_lesson_items
    │       ├──▶ VTTExtractionService.extract_vtt(video_url)
    │       │       ├──▶ HTTP GET Kinescope embed HTML
    │       │       ├──▶ Regex extract playerOptions → .vtt URLs
    │       │       ├──▶ HTTP GET VTT content
    │       │       └──▶ _parse_vtt() → clean text
    │       └──▶ Save raw_vtt to conspects (or temp)
    │
    ├──▶ TextCompressionService.compress(raw_vtt)
    │       └──▶ sumy LexRank → compressed_text (30% of original)
    │
    ├──▶ status = 'generating'
    │       └──▶ LLMSummaryService.generate_conspect(compressed_text, title)
    │               ├──▶ Build structured prompt
    │               ├──▶ OpenRouter API call (deepseek-v3.2)
    │               ├──▶ Parse JSON response
    │               └──▶ Pydantic validation (ConspectContent)
    │
    ├──▶ INSERT INTO conspects (topic, summary, key_points, definitions, difficulty, ...)
    │
    └──▶ status = 'ready', conspect_id = <new conspect id>
    │
    ▼
Frontend poll sees status='ready' → fetch conspect → display
```

## Cost Optimization Pipeline

```
Raw VTT (60 min webinar)
    │ ~30,000 tokens
    ▼
Parse VTT (remove timestamps, dedup)
    │ ~25,000 tokens  (17% reduction)
    ▼
Extractive summarization (sumy LexRank, target_ratio=0.3)
    │ ~7,500 tokens  (70% reduction from raw)
    ▼
LLM prompt (system + compressed text + instructions)
    │ ~8,000 tokens input
    ▼
OpenRouter deepseek-v3.2
    │ ~$0.002 per 1K input tokens
    │ Input:  $0.016
    │ Output: ~2,000 tokens @ $0.008 = $0.016
    │ TOTAL:  ~$0.032 per conspect
```

**Target:** ≤ $0.05 per 60-min webinar conspect ✅

## API Endpoints (Phase 2 — implemented)

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/api/summary/programs` | ✅ Real data from DB + sync on miss |
| GET | `/api/summary/programs/{id}/modules` | ✅ Real data from DB |
| GET | `/api/summary/modules/{id}/lessons` | ✅ Real data from DB |
| GET | `/api/summary/lessons/{id}/items` | ✅ Filter `video`/`webinar` + has_vtt |
| POST | `/api/summary/conspects/generate` | ✅ Creates job + enqueues ARQ task |
| GET | `/api/summary/jobs/{id}` | ✅ Returns job status |

## Error Handling Strategy

| Scenario | Handling |
|----------|----------|
| Kinescope HTML changed, VTT not found | Status → `failed`, error = "VTT не найдены", user sees retry button |
| OpenRouter rate limit / timeout | ARQ retry 3x, then `failed`, error = "LLM недоступен" |
| VTT > 100KB (very long webinar) | Skip extractive, send directly to LLM with chunking |
| LLM returns invalid JSON | Retry once with "fix JSON" prompt, then `failed` |
| Netology API 401 (session expired) | Return 401 to frontend, trigger re-auth |
| Redis unavailable | Jobs fail immediately, status = `failed`, alert admin |

## Frontend (Phase 2 — minimal)

```
GenerateConspectModal:
  Step 1: Select program (dropdown, fetched from /api/summary/programs)
  Step 2: Select module (dropdown, fetched from /api/summary/programs/{id}/modules)
  Step 3: Select webinar (dropdown, fetched from /api/summary/modules/{id}/lessons/{id}/items)
  
  On submit:
    - POST /api/summary/conspects/generate
    - Close modal, show toast "Конспект генерируется"
    - Start polling GET /api/summary/jobs/{id} every 2s
    - On ready: redirect to /conspects/{id}
    - On failed: show error, allow retry
```

## File Structure (new/changed)

```
backend/
  services/
    netology_program_service.py      # Sync + fetch from Netology API
    vtt_extraction_service.py        # Already exists, may need async HTTP
    text_compression_service.py      # NEW: sumy LexRank wrapper
    llm_summary_service.py           # NEW: LLM provider + generation
    conspect_job_service.py          # NEW: Job orchestration
  workers/
    summary_worker.py                # NEW: ARQ worker entry point
  api/
    summary_router.py                # UPDATE: implement endpoints
  schemas/
    summary.py                       # UPDATE: add ConspectContent schema
frontend/src/
  components/
    GenerateConspectModal.tsx        # NEW: 3-step modal
    JobStatusToast.tsx               # NEW: status polling toast
  api/
    summary.ts                       # NEW: API client for summary endpoints
```

## Technology Decisions (reaffirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Background jobs | ARQ + Redis | Already in requirements, type-safe, simple |
| Extractive summarization | `sumy` (LexRank) | Lightweight, no ML model download, fast |
| LLM | OpenRouter deepseek-v3.2 | API key already in `.env`, cheap, good Russian |
| Structured output | Pydantic + prompt template | Validates output, typed frontend |
| HTTP client for VTT | `httpx` (async) | Already used in project |

## Open Questions

1. **Should we auto-sync programs on first load or require manual "Обновить" button?**
   - Proposal: Manual sync button in modal. Auto-sync on first visit is slow and may fail.
   
2. **Should we cache VTT text in `netology_lesson_items` or only in `conspects.raw_vtt`?**
   - Proposal: Cache in `netology_lesson_items.raw_vtt` (new nullable column) to avoid re-fetching for re-generation. But this adds storage. Keep only in `conspects` for MVP.
   
3. **Chunking strategy for very long webinars (>2 hours)?**
   - Proposal: If compressed text > 8K tokens, split into chunks, generate per-chunk summaries, then combine with a final "merge" LLM call. Defer to Phase 5 if needed.

## Acceptance Criteria (Phase 2)

1. User opens modal → sees programs → selects → sees modules → selects → sees webinars.
2. User clicks generate → sees toast "Генерируется" → poll updates.
3. Within 3 minutes, status changes to "Готов" → user sees conspect.
4. Conspect contains: topic, summary, key_points, definitions, difficulty (all from LLM).
5. Cost per conspect ≤ $0.05 (measured via OpenRouter usage dashboard).
6. If VTT not found → clear error message, no infinite spinner.
7. If LLM fails → retry 3x, then clear error.

---

**Please review and approve or request changes before implementation starts.**
