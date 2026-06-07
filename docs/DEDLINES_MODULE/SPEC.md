# SDD: Модуль «Ближайшие события и дедлайны»

**Версия:** 1.1  
**Дата:** 2026-06-23  
**Статус:** Согласовано  

---

## 1. Цель

Создать модуль для отслеживания **предстоящих** дедлайнов, зачётов, экзаменов и занятий пользователя на платформе Netology.

**Проблемы предыдущего модуля (откат):**
- Дубли не убирались (4 записи вместо 1 на одну дату)
- Пропали фильтры
- Неправильная фильтрация семестра
- Исчезли ДЗ
- Смешение типов (тест, ДЗ, вебинар, зачёт) в одной куче

---

## 2. Архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Модуль «Ближайшие события и дедлайны»               │
│                         Frontend (Vite + React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │ Виджет       │  │ Фильтры      │  │ Модуль «Календарь»           │  │
│  │ «Дедлайны»   │  │ (категории)  │  │ (полная таблица / сетка)     │  │
│  │              │  │              │  │ — тут ВСЁ, включая прошлое   │  │
│  │ Только       │  │              │  │                              │  │
│  │ БУДУЩЕЕ      │  │              │  │                              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Router       │  │ Service      │  │ Merger       │  │ DB Models  │ │
│  │ /deadlines   │  │ NetologyAPI  │  │ + Grouper    │  │ PostgreSQL │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌─────────────────────┐          ┌─────────────────────┐
        │ /student_learning   │          │ /programs/{id}      │
        │ /calendar           │          │ /schedule           │
        └─────────────────────┘          └─────────────────────┘
                    │                               │
              Task + Webinar                   Task + Test + Webinar
              (точные даты)                    (дедлайн в title)
```

---

## 3. Источники данных

| Endpoint | Что даёт | Чего нет |
|----------|----------|----------|
| `GET /backend/api/user/student_learning/calendar` | task (ДЗ), webinar (вебинары, зачёты, экзамены) | **test (тесты)** |
| `GET /backend/api/user/programs/{id}/schedule` | task, test, webinar, video, text, attachment | Не все события, дедлайн в `title` |

**Стратегия:** использовать **оба** endpoint'а, merge + deduplicate.

**Важно:** полные сырые ответы endpoint'ов **не храним**. В БД сохраняем только результат обработки — сгруппированные события. `raw_items` (JSONB) содержит только item'ы конкретной группы (для детализации в календаре).

### 3.1 Поля из calendar
```json
{
  "id": 123,
  "lesson_id": 456,
  "type": "task|webinar",
  "title": "Название",
  "starts_at": "2026-06-02T14:20:00.000Z",
  "ends_at": "2026-06-02T15:55:00.000Z",
  "status": "passed|approved",
  "lesson_task": {
    "deadline": "2026-06-02T20:59:00.000Z",
    "homework": { "status": "waiting_review", "score": null }
  }
}
```

### 3.2 Поля из program schedule
```json
{
  "id": 789,
  "type": "task|test|webinar",
  "title": "Название (до 02.06.2026)",
  "passed": true|false,
  "path": "/..."
}
```

---

## 4. Модель данных (PostgreSQL)

### 4.1 Таблица `deadline_events`

Хранит **сгруппированные** события (не сырые item'ы).

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | Уникальный ID группы |
| `user_id` | UUID FK → user_sessions | Пользователь |
| `lesson_id` | INT | Группировочный ключ из API |
| `event_type` | ENUM | `task` / `test` / `webinar` |
| `sub_type` | ENUM | `lesson` / `consultation` / `credit` / `exam` |
| `title` | VARCHAR(500) | Нормализованное название |
| `program_title` | VARCHAR(500) | Название программы/модуля |
| `date` | DATE | Дата события |
| `time` | TIME | Время начала (для webinar), с припиской «МСК» |
| `status` | ENUM | `pending` / `approved` / `passed` / `overdue` |
| `source` | ENUM | `calendar` / `schedule` / `merged` |
| `raw_items` | JSONB | Сырые item'ы группы (для деталей в календаре) |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

### 4.2 Таблица `deadline_sync_log`

Лог последней синхронизации.

| Поле | Тип |
|------|-----|
| `user_id` | UUID PK |
| `last_sync_at` | TIMESTAMP |
| `events_count` | INT |
| `source_checksum` | VARCHAR(64) |

---

## 5. Алгоритм группировки (Вариант А)

### Шаг 1: Нормализация title
```python
def normalize_title(title: str) -> str:
    """Убирает суффиксы групп, вариантов, попыток."""
    title = re.sub(r'\.\s*Вариант\s*[\w№]+', '', title, flags=re.I)
    title = re.sub(r'\.\s*Попытка\s*[\w№]+', '', title, flags=re.I)
    title = re.sub(r'[\.\s]*\d+\s*группа', '', title, flags=re.I)
    title = re.sub(r'\s+', ' ', title).strip('. ')
    return title
```

### Шаг 2: Группировка
```python
def group_items(items: list[dict]) -> list[EventGroup]:
    """Группирует по (lesson_id, type, normalized_title)."""
    groups = defaultdict(list)
    
    for item in items:
        key = (
            item["lesson_id"],                    # ← главный ключ
            item["type"],                         # task / test / webinar
            normalize_title(item["title"])        # для читаемости
        )
        groups[key].append(item)
    
    return [merge_group(g) for g in groups.values()]
```

### Шаг 3: Merge группы в одно событие
```python
def merge_group(items: list[dict]) -> EventGroup:
    """Сливает item'ы группы в одно событие."""
    # Дата: минимальная из всех
    dates = [parse_date(i) for i in items if parse_date(i)]
    date = min(dates) if dates else None
    
    # Статус: passed если хоть один passed
    statuses = [i.get("status") or i.get("passed") for i in items]
    is_passed = any(s in ("passed", True, "approved") for s in statuses)
    
    return EventGroup(
        title=normalize_title(items[0]["title"]),
        date=date,
        status="passed" if is_passed else "pending",
        raw_items=items,
        item_count=len(items),
    )
```

---

## 6. Определение sub_type (Зачёт/Экзамен/Консультация)

API возвращает `type: "webinar"` для всех. Подтип определяем по title:

```python
def detect_sub_type(title: str, event_type: str) -> str:
    """Определяет подтип по ключевым словам в title."""
    if event_type != "webinar":
        return "lesson"  # Для task/test подтипа нет
    
    title_lower = title.lower()
    if "экзамен" in title_lower:
        return "exam"
    if "зачёт" in title_lower or "зачет" in title_lower:
        return "credit"
    if "консультация" in title_lower:
        return "consultation"
    return "lesson"
```

---

## 7. Фильтры (Frontend)

**Порядок фильтров (слева направо / сверху вниз):**

| # | Фильтр | Категория | Типы API | sub_type |
|---|--------|-----------|----------|----------|
| 1 | **📅 Занятия** | Обычные вебинары, уроки, консультации | webinar | lesson, consultation |
| 2 | **📝 Работы** | ДЗ, тесты, задания | task, test | — |
| 3 | **🎓 Контроль** | Зачёты, экзамены | webinar | credit, exam |
| 4 | **Все** | Всё сгруппированное | task, test, webinar | все |

**По умолчанию:** фильтр «📅 Занятия» или «Все» (обсудить), сортировка по дате (ближайшие сверху).

---

## 8. Правило отображения: ТОЛЬКО БУДУЩЕЕ

**Критическое правило:** модуль «Ближайшие события и дедлайны» отображает **только события в будущем** относительно текущего момента.

- ❌ **Не отображаем:** прошедшие вебинары, просроченные дедлайны, завершённые зачёты
- ✅ **Отображаем:** только то, что ещё не случилось (starts_at / deadline > now)
- 📅 **Где прошлое:** в модуле «Календарь» или в отдельном модуле напоминаний (в будущем)

**Реализация:** фильтр `date >= NOW()` на уровне SQL-запроса.

---

## 9. Время

- Берём время **как указано на Netology** (из `starts_at`, `ends_at`, `deadline`)
- Отображаем с припиской **«МСК»** (без конвертации часового пояса)
- Пример: `14:20 МСК`

---

## 10. Синхронизация

| Параметр | Значение |
|----------|----------|
| **Частота** | Каждые 30 минут (фоновая) + ручная (по кнопке) |
| **Стратегия записи** | Upsert: старые события пользователя удаляются, новые вставляются |
| **Что храним** | Только сгруппированные события (`deadline_events`), не полные ответы API |

**Алгоритм синхронизации:**
1. Запросить оба endpoint'а
2. Merge + group + dedup
3. `DELETE FROM deadline_events WHERE user_id = ?`
4. `INSERT INTO deadline_events ...` (batch insert)
5. Записать `deadline_sync_log`

---

## 11. Модуль «Календарь» (отдельная страница)

Полная таблица/сетка **всех** событий (включая дубли и прошлое).

- **Вид:** таблица или сетка по неделям
- **Детализация:** можно раскрыть группу и увидеть «Вариант 1 — ✅, Вариант 2 — ❌»
- **Фильтры:** те же 4 категории + по программе
- **Навигация:** месяц / неделя / день

---

## 12. API Endpoints (Backend)

### 12.1 Синхронизация
```
POST /api/deadlines/sync
→ Запускает синхронизацию с Netology API
→ Сохраняет grouped events в БД (upsert)
→ Возвращает { synced: N, duration_ms: 1234 }
```

### 12.2 Получение ближайших событий
```
GET /api/deadlines?filter=lessons|works|control|all&days=30&from=2026-06-23
→ Возвращает EventGroup из БД с фильтром date >= NOW()
→ Пагинация: offset + limit
```

### 12.3 Получение календаря
```
GET /api/deadlines/calendar?month=2026-06&filter=all
→ Возвращает события по дням (для сетки календаря)
→ Включает дубли (raw_items раскрыт)
→ **Без фильтра date >= NOW()** — показывает всё
```

### 12.4 Получение одного события
```
GET /api/deadlines/{event_id}
→ Детали группы с raw_items
```

---

## 13. Задачи реализации

### Этап 1: База данных
- [ ] Создать таблицы `deadline_events`, `deadline_sync_log`
- [ ] Alembic миграция

### Этап 2: Backend — Core
- [ ] Сервис `NetologyCalendarService` (запрос к `/student_learning/calendar`)
- [ ] Сервис `NetologyScheduleService` (запрос к `/programs/{id}/schedule`)
- [ ] Модуль `deadline_merger` (merge + group + dedup)
- [ ] Модуль `title_normalizer` (normalize_title + detect_sub_type)

### Этап 3: Backend — API
- [ ] Router `POST /api/deadlines/sync`
- [ ] Router `GET /api/deadlines` (с фильтром `date >= NOW()`)
- [ ] Router `GET /api/deadlines/calendar` (без фильтра по дате)
- [ ] Router `GET /api/deadlines/{event_id}`

### Этап 4: Frontend — Виджет «Ближайшие события и дедлайны»
- [ ] Компонент списка событий
- [ ] Фильтры (Занятия / Работы / Контроль / Все)
- [ ] Карточка события (title, date + «МСК», status, program)
- [ ] Кнопка «Синхронизировать»
- [ ] Авто-скрытие прошедших (данные отфильтрованы на бэке)

### Этап 5: Frontend — Модуль «Календарь»
- [ ] Сетка календаря (месяц)
- [ ] Раскрытие групп (детали дублей)
- [ ] Фильтры по категории и программе

### Этап 6: Интеграция и тесты
- [ ] E2E тест: синхронизация → отображение
- [ ] Тест группировки (mock данные с дублями)
- [ ] Тест фильтра `date >= NOW()`
- [ ] Тест фильтров по категориям

---

## 14. Решения (итог)

| Решение | Обоснование |
|---------|-------------|
| Два источника → merge | Calendar даёт точные даты, Schedule даёт тесты |
| Группировка по `lesson_id` | API сама группирует дубли |
| `sub_type` из title | API не даёт отдельного поля |
| 4 фильтра (Занятия→Работы→Контроль→Все) | Порядок по важности действия |
| **Только будущее** | Модуль не перегружается прошлым |
| Время + «МСК» | Как на Netology, без усложнения TZ |
| Синхронизация каждые 30 мин | Актуальность без нагрузки |
| Upsert (замена, не накопление) | БД не растёт бесконтрольно |
| Уведомления — позже | Отдельный этап после стабилизации |
| Отдельный модуль «Календарь» | Полная история без перегрузки виджета |
| JSONB `raw_items` | Детали дублей для календаря и отладки |
