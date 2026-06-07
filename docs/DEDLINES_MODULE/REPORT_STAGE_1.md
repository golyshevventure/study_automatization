# Отчёт: Этап 1 — База данных

**Дата:** 2026-06-05  
**Статус:** ✅ Завершён  

---

## Что сделано

### 1.1 Созданы модели SQLAlchemy

**Файл:** `backend/models/deadline_event.py`

Две модели в стиле SQLAlchemy 2.0 (Mapped, mapped_column):

#### `DeadlineEvent`
| Поле | Тип | Назначение |
|------|-----|------------|
| `id` | UUID PK (v7) | Уникальный ID группы |
| `user_id` | UUID FK → user_sessions | Пользователь |
| `lesson_id` | INT | Группировочный ключ из API |
| `event_type` | VARCHAR(20) | `task` / `test` / `webinar` |
| `sub_type` | VARCHAR(20) | `lesson` / `consultation` / `credit` / `exam` |
| `title` | VARCHAR(500) | Нормализованное название |
| `program_title` | VARCHAR(500) | Название программы |
| `event_date` | DATE | Дата события |
| `event_time` | TIME | Время начала (для вебинаров) |
| `status` | VARCHAR(20) | `pending` / `approved` / `passed` / `overdue` |
| `source` | VARCHAR(20) | `calendar` / `schedule` / `merged` |
| `raw_items` | JSONB | Сырые item'ы группы |
| `created_at` | TIMESTAMPTZ | Авто |
| `updated_at` | TIMESTAMPTZ | Авто |

**Индексы:** `user_id`, `event_type`, `sub_type`, `status`, `event_date`

#### `DeadlineSyncLog`
| Поле | Тип | Назначение |
|------|-----|------------|
| `user_id` | UUID PK/FK | Пользователь |
| `last_sync_at` | TIMESTAMPTZ | Время синхронизации |
| `events_count` | INT | Количество событий |
| `source_checksum` | VARCHAR(64) | Контрольная сумма |

### 1.2 Обновлены импорты

- `backend/models/__init__.py` — добавлены `DeadlineEvent`, `DeadlineSyncLog`
- `backend/alembic/env.py` — добавлен импорт новых моделей для autogenerate

### 1.3 Создана и применена миграция Alembic

**Миграция:** `4b42fea88b8e_add_deadline_events_and_sync_log.py`

**Что включает:**
- `CREATE TABLE deadline_events`
- `CREATE TABLE deadline_sync_log`
- 5 индексов на `deadline_events`
- `DROP COLUMN user_sessions.deadlines_cached_at`
- `DROP COLUMN user_sessions.deadlines_cache_json` (остатки старого модуля)

**Применена:** `alembic upgrade head` ✅

### 1.4 Очищены остатки старого модуля

Удалены файлы предыдущей (откаченной) реализации:
- `backend/services/netology_deadlines_service`
- `frontend/src/types/deadline.ts`
- `frontend/src/utils/deadlineUtils.ts`

### 1.5 Проверка БД

```
Tables: ['alembic_version', 'deadline_events', 'deadline_sync_log', 'user_sessions']

Indexes on deadline_events:
  deadline_events_pkey
  ix_deadline_events_event_date
  ix_deadline_events_event_type
  ix_deadline_events_status
  ix_deadline_events_sub_type
  ix_deadline_events_user_id
```

---

## Проблемы и решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| `Can't locate revision identified by 'ab6e970cd7f0'` | В БД осталась версия от удалённой миграции старого модуля | Обновили `alembic_version` на актуальный `head` (`673585175e4d`) |

---

## Следующий этап

**Этап 2:** Backend Core — сервисы для запросов к Netology API, merger, title normalizer.
