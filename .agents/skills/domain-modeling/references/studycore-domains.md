# StudyCore Domain Map

## Bounded Contexts

### 1. Deadlines Context

**Language:** event, sync, deadline, schedule, calendar

**Entities:**
- `DeadlineEvent` — id, user_id, title, event_date, event_type, program_title, status
- `DeadlineSyncLog` — id, user_id, sync_status, items_count, error_message, created_at

**Value Objects:**
- `EventType` — enum: lesson, consultation, work, test, exam, credit
- `EventDate` — normalized date with timezone

**Aggregate:** `DeadlineEvent` (root) + related variants

**Domain Services:**
- `DeadlineMerger` — merge and group duplicate events
- `DeadlineSyncService` — orchestrate sync with Netology

**Domain Events:**
- `SyncStarted`
- `SyncCompleted`
- `SyncFailed`

---

### 2. Auth Context

**Language:** session, token, user, cookie, csrf

**Entities:**
- `UserSession` — id, user_id, cookies, csrf_token, is_active, created_at

**Value Objects:**
- `Cookies` — wrapper for session cookie data

**Domain Services:**
- `NetologyAuthService` — authenticate with Netology platform
- `SessionManager` — validate and refresh sessions

---

### 3. Programs Context

**Language:** program, discipline, profession, lesson, course

**Entities:**
- `Program` — id, title, status, enrolled_at
- `Discipline` — id, program_id, title, order
- `Lesson` — id, discipline_id, title, type, duration

**Value Objects:**
- `ProgramStatus` — enum: active, completed, paused

---

### 4. Materials Context

**Language:** material, conspect, transcription, summary, audio

**Entities:**
- `Material` — id, lesson_id, type, url, status
- `Transcription` — id, material_id, text, language, created_at

**Value Objects:**
- `MaterialType` — enum: video, audio, pdf, link
- `Language` — ru, en

**Domain Services:**
- `AudioExtractor` — extract audio from video
- `TranscriptionService` — transcribe audio to text
- `SummaryGenerator` — generate summary from transcription

---

## Context Mapping

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Auth     │────→│  Programs   │────→│  Deadlines  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                     ↑
       └─────────────────────────────────────┘
                    (sync uses auth)

┌─────────────┐
│  Materials  │←───── Programs (lesson reference)
└─────────────┘
```

**Relationships:**
- Auth → Deadlines: Customer/Supplier (Deadlines depends on Auth for user identification)
- Programs → Deadlines: Customer/Supplier (Deadlines syncs program schedules)
- Programs → Materials: Customer/Supplier (Materials reference program lessons)

## Shared Kernel

- `UserId` — UUID string, used across all contexts
- `ProgramId` — integer ID from Netology, used in Programs and Deadlines
