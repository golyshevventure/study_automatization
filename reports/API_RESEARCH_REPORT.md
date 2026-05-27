# 🔬 Исследование API Нетологии — ОТЧЁТ

> Дата: 22.05.2026
> Исследователь: StudyCore AI Agent
> Метод: Playwright network interception + httpx API testing

---

## 🎯 Главный вывод

**Весь контент Нетологии доступен через REST API.** Playwright нужен только для авторизации (получения cookies). После авторизации — только HTTP-запросы.

**Ожидаемое ускорение:** с 17 часов до **30-60 минут** на весь бакалавриат.

---

## 📡 Найденные API Endpoint'ы

### 1. Структура профессии (все программы)

```
GET /backend/api/user/professions/{profession_id}/schedule
```

**Что возвращает:**
- `name`: "Бакалавриат «Финансы и анализ данных»..."
- `profession_modules[]`: список модулей (23 шт.)
  - `program.id`: числовой ID программы (69757, 70599, ...)
  - `program`: {id, name, duration, ...}

**Пример:**
```json
{
  "name": "Бакалавриат «Финансы и анализ данных»...",
  "profession_modules": [
    {
      "id": 157464,
      "program": {
        "id": 69757,
        "name": null,
        ...
      }
    }
  ]
}
```

---

### 2. Расписание программы (список занятий)

```
GET /backend/api/user/programs/{program_id}/schedule
```

**Что возвращает:**
- `lessons[]`: список занятий
  - `id`: ID урока
  - `title`: название
  - `type`: тип (common, regular, ...)
  - `starts_at`: дата начала
  - `locked`: заблокирован ли
  - `lesson_items[]`: список материалов!

**Пример:**
```json
{
  "lessons": [
    {
      "id": 530688,
      "title": "Встречи с командой программы",
      "type": "common",
      "locked": false,
      "lesson_items": [
        {
          "id": 530688,
          "title": "Еженедельный план обучения. 6 неделя",
          "type": "text",
          "video_url": null,
          "webinar_url": null,
          "youtube_video_id": null,
          "path": "/profile/program/.../lesson_items/530688"
        }
      ]
    }
  ]
}
```

**Ключевое:** `lesson_items` уже есть в schedule! Не нужен отдельный запрос на список.

---

### 3. Контент материала (текст)

```
GET /backend/api/user/lesson_items/{item_id}
```

**Что возвращает:**
- `title`: заголовок
- `content`: текст материала (Markdown!)
- `content_type`: "markdown"
- `type`: "text" | "video" | ...
- `video_url`: URL видео (если есть)
- `webinar_url`: URL вебинара (если есть)
- `youtube_video_id`: ID YouTube (если есть)
- `locked`: заблокирован ли
- `passed`: пройден ли

**Пример:**
```json
{
  "id": 530688,
  "title": "Еженедельный план обучения. 6 неделя",
  "content": "**С 29 ноября по 5 декабря**\n\n1. Изучите материалы...",
  "content_type": "markdown",
  "type": "text",
  "video_url": null,
  "webinar_url": null,
  "youtube_video_id": null,
  "locked": false,
  "passed": false
}
```

---

### 4. Информация о программе

```
GET /backend/api/user/programs/{slug_or_id}
```

**Примеры:**
- `GET /backend/api/user/programs/bhebfad-25` — по slug
- `GET /backend/api/user/programs/bhebfad-25-memeo-2` — по slug
- `GET /backend/api/user/programs/69757` — по числовому ID

**Возвращает:** метаданные программы (название, даты, цена, доступы)

---

### 5. Прогресс обучения

```
GET /backend/api/user/programs/progress
```

**Возвращает:** прогресс по всем программам (38KB JSON)

---

### 6. Календарь

```
GET /backend/api/user/student_learning/calendar
```

**Возвращает:** календарь всех программ (370KB JSON!)

---

### 7. Уведомления / Сообщения

```
GET /backend/api/user/notifications/unread_messages
```

**Возвращает:** список сообщений из ЛК (для AI-сортировки)

---

## 🏗️ Новая архитектура (API-first)

```
[Playwright] → Авторизация + получение cookies (1 раз)
     ↓
[httpx.AsyncClient] → HTTP API запросы
     ↓
┌─────────────────────────────────────────────┐
│  1. GET /professions/{id}/schedule          │
│     → profession_modules[]                  │
│     → program.id для каждой дисциплины      │
│                                             │
│  2. Для каждой программы:                   │
│     GET /programs/{id}/schedule             │
│     → lessons[]                             │
│     → lesson_items[]                        │
│                                             │
│  3. Для каждого lesson_item:                │
│     GET /lesson_items/{id}                  │
│     → content (markdown!)                   │
│     → video_url (если есть)                 │
│                                             │
│  4. VTT: извлекаем по video_url             │
│     (или через Kinescope API)               │
└─────────────────────────────────────────────┘
     ↓
[LLM] → Генерация конспектов
     ↓
[PostgreSQL] → Хранение
     ↓
[Mini App] → Отображение
```

---

## ⏱️ Оценка скорости

| Этап | Playwright | API-first | Ускорение |
|------|-----------|-----------|-----------|
| Открыть страницу | 3-5 сек | 50-200 мс | **20x** |
| Получить структуру | 10-30 сек | 200-500 мс | **30x** |
| Получить контент урока | 5-10 сек | 50-200 мс | **30x** |
| Получить VTT | 2-5 сек | 50-200 мс | **20x** |
| **Итого на дисциплину** | **30 мин** | **~1 мин** | **30x** |
| **Итого на бакалавриат** | **17 часов** | **~30 мин** | **34x** |

---

## ⚠️ Что нужно проверить

1. **VTT через API** — можно ли получить субтитры без Playwright?
   - Вариант A: video_url → Kinescope API для VTT
   - Вариант B: youtube_video_id → YouTube API для транскрипции
   - Вариант C: оставить VTT-перехват на Playwright как fallback

2. **Авторизация** — как долго живут cookies?
   - Нужно тестировать: авторизоваться, подождать 24ч, проверить

3. **Rate limits** — есть ли ограничения на API?
   - Пока не замечено, но нужно тестировать под нагрузкой

4. **Блокированные уроки** — API отдаёт `locked=true`, но отдаёт ли content?
   - Нужно проверить: запросить locked урок

---

## 📁 Файлы исследования

| Файл | Описание |
|------|----------|
| `Данные/api_explore.json` | Все 405 перехваченных запросов |
| `Данные/api_test_report.json` | Результаты тестирования 15 endpoint'ов |
| `Данные/api_*_schedule.json` | JSON ответы API |
| `docs/API_RESEARCH_REPORT.md` | Этот отчёт |

---

## 🚀 Следующие шаги

1. **Создать `netology_api_client.py`** на httpx
2. **Реализовать API-first прогон** одной дисциплины
3. **Сравнить скорость** с Playwright
4. **Проверить VTT** без Playwright
5. **Если всё ок** — удалить Playwright из основного пайплайна

---

*Исследование завершено. API Нетологии — открыт и работает.*
