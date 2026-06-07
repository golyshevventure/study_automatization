# Отчёт: Этап 3 — Backend API

**Дата:** 2026-06-05  
**Статус:** ✅ Завершён  

---

## Что сделано

### 3.1 Pydantic-схемы

**Файл:** `backend/schemas/deadline.py`

| Схема | Назначение |
|-------|------------|
| `DeadlineEventResponse` | Базовый ответ события (id, type, sub_type, title, date, status, item_count) |
| `DeadlineEventDetailResponse` | Детали с raw_items |
| `DeadlineSyncResponse` | Результат синхронизации |
| `DeadlineListResponse` | Список событий + total + filter |

### 3.2 Сервис `deadline_service.py`

**Файл:** `backend/services/deadline_service.py`

| Метод | Описание |
|-------|----------|
| `sync(user_id, cookies)` | Запрос к Netology → merge → upsert в БД |
| `list_events(user_id, filter, limit, offset)` | Чтение из БД с фильтром `date >= NOW()` |
| `get_event(user_id, event_id)` | Одно событие по ID |

**Upsert-стратегия:**
1. `DELETE FROM deadline_events WHERE user_id = ?`
2. Batch INSERT новых событий
3. `INSERT ... ON CONFLICT UPDATE` в `deadline_sync_log`

### 3.3 Роутер `deadlines_router.py`

**Файл:** `backend/api/deadlines_router.py`

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/deadlines/sync` | POST | Синхронизация с Netology API |
| `/api/deadlines?filter=...` | GET | Список будущих событий |
| `/api/deadlines/{event_id}` | GET | Детали одного события |

**Фильтры:**
- `all` — всё
- `lessons` — webinar с sub_type = lesson / consultation
- `works` — task + test
- `control` — webinar с sub_type = credit / exam

### 3.4 Подключение

- `backend/main.py` — добавлен `deadlines_router`

---

## Результаты тестирования API

### GET /api/deadlines?filter=all
```json
{
  "events": [...],
  "total": 5,
  "filter": "all"
}
```

### GET /api/deadlines?filter=works
- Тесты: «Тест текущего контроля», «Тест на зачет», «Экзаменационный тест»

### GET /api/deadlines?filter=control
- Зачёты: «Зачет (подключение...)», «Иностранный язык. Зачёт», «БЖД»...

### GET /api/deadlines?filter=lessons
- Занятия: «Логика», «Философия», «Иностранный язык»

### POST /api/deadlines/sync
```json
{
  "synced": 552,
  "duration_ms": 57006,
  "message": "Синхронизировано 552 событий"
}
```

---

## Проблемы и решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| Pydantic: `id` UUID → string | `model_validate` получал UUID объект | Схема: `id: UUID` вместо `str` |
| Pydantic: `item_count` missing | Поля нет в ORM модели | `computed_field` на `raw_items` с `Field(exclude=True)` |
| Server import error | uvicorn запущен из `backend/`, PYTHONPATH не включал корень | Запуск из корня с `PYTHONPATH=. uvicorn backend.main:app` |

---

## Следующий этап

**Этап 4:** Frontend — виджет «Ближайшие события и дедлайны»
