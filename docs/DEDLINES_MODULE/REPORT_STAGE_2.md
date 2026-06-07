# Отчёт: Этап 2 — Backend Core

**Дата:** 2026-06-05  
**Статус:** ✅ Завершён  

---

## Что сделано

### 2.1 `title_normalizer.py`

**Файл:** `backend/services/title_normalizer.py`

Чистые функции без зависимостей:

- **`normalize_title(title)`** — убирает «Вариант N», «Попытка №N», «N группа»
- **`detect_sub_type(title, event_type)`** — определяет подтип webinar по ключевым словам:
  - «экзамен» → `exam`
  - «зачёт/зачет» → `credit`
  - «консультация» → `consultation`
  - остальное → `lesson`

### 2.2 `netology_calendar_service.py`

**Файл:** `backend/services/netology_calendar_service.py`

- Endpoint: `GET /student_learning/calendar`
- Извлекает `task` (с дедлайном из `lesson_task.deadline`) и `webinar` (с датой из `starts_at`)
- Определяет статус: `passed` / `approved` / `pending`
- Нормализует item'ы в единообразный формат

### 2.3 `netology_schedule_service.py`

**Файл:** `backend/services/netology_schedule_service.py`

- **Ключевое открытие:** для профессий/бакалавриата `/programs/{id}/schedule` возвращает 0 lessons.
  Нужно сначала запросить `/professions/{id}/schedule`, извлечь `profession_modules[].program.id`,
  а затем для каждого program_id запросить `/programs/{id}/schedule`.
- Парсит дедлайн из title (форматы: "до ДД.ММ.ГГГГ", "Дедлайн ДД.ММ.ГГГГ", "Дедлайн — ДД.ММ")
- Для дат без года — эвристика: если дата в прошлом > 30 дней, берём следующий год
- Извлекает `task`, `test`, `webinar`
- Обработка таймаутов (`httpx.ReadTimeout`)

### 2.4 `deadline_merger.py`

**Файл:** `backend/services/deadline_merger.py`

- **`merge_sources()`** — объединяет item'ы по `id`. Calendar приоритетнее для дат.
- **`group_items()`** — группировка по `(lesson_id, type, normalized_title)`.
  - Дата: минимальная из группы
  - Статус: `passed` если хоть один `passed`
- **`build_deadline_events()`** — полный pipeline: merge → group → sort by date

---

## Результаты тестирования (живые данные)

| Метрика | Значение |
|---------|----------|
| Calendar items | 539 |
| Schedule items | 598 |
| **Grouped events** | **551** |
| Future events | 91 |
| — webinar | 16 |
| — test | 32 |
| — task | 43 |
| Multi-item groups | 7 |

**Примеры группировки:**
- «Тест текущего контроля» — **6 items** (2 варианта × 3 попытки)
- «Зачёт. Иностранный язык» — **2 items** (1 и 2 группа)
- «Тест на зачёт» (Логика) — **3 items** (3 попытки)
- «Экзаменационный тест» (Мировая экономика) — **3 items** (3 попытки)

---

## Проблемы и решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| Schedule возвращает 0 lessons для profession_id | API отдаёт schedule по отдельным курсам (program_id), не по profession | Добавлен двухуровневый запрос: profession → modules → program.id → schedule |
| Таймауты при запросе 20+ program schedules | Много последовательных HTTP-запросов | Увеличен timeout до 60s, добавлена обработка `ReadTimeout` |
| Даты без года в title ("Дедлайн 24 марта") | API не указывает год для старых курсов | Добавлен regex для формата без года + эвристика года |
| Тестовые даты в прошлом | Парсинг дат без timezone | Все datetime теперь в `timezone.utc` |

---

## Следующий этап

**Этап 3:** Backend API — роутеры `/deadlines/*`
