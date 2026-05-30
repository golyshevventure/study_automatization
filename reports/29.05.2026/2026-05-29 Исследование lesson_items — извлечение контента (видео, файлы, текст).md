# Исследование: Извлечение контента из lesson_items Netology

**Дата:** 2026-05-29  
**Контекст:** StudyCore нужно получать контент учебных материалов (видео, файлы, текст) напрямую через API Netology, без Playwright. Исследован endpoint `GET /backend/api/user/lesson_items/{id}` и способы извлечения медиа.

---

## Что исследовано

1. **Endpoint `GET /backend/api/user/lesson_items/{id}`**
   - Возвращает детальную информацию о любом учебном элементе
   - Требует авторизации (cookies `_netology-on-rails_session`)
   - Не требует CSRF-токена для GET-запросов

2. **Обход структуры программ**
   - `calendar/filters` → список программ
   - `professions/{id}/schedule` → profession_modules → program (id)
   - `programs/{program_id}/schedule` → lessons → lesson_items

3. **Типы lesson_items и способы извлечения контента**

4. **Извлечение видео из Kinescope**
   - Парсинг embed-страницы → `playerOptions.playlist[0].sources.hls.src`
   - Получение master.m3u8 (HLS playlist)

---

## Архитектура обхода

```
Пользователь
    ↓
NetologyAuthService.authenticate()
    ↓ POST /sign_in + cookies
Netology.ru
    ↓
GET /backend/api/user/programs/calendar/filters
    ↓ список программ
GET /backend/api/user/professions/{prof_id}/schedule
    ↓ profession_modules[]
GET /backend/api/user/programs/{mod_prog_id}/schedule
    ↓ lessons[] → lesson_items[]
GET /backend/api/user/lesson_items/{id}
    ↓ JSON с контентом
StudyCore
```

### Почему именно такой обход

- Программы типа `paid` (бакалавриат) хранят уроки внутри `profession_modules`
- Каждый модуль содержит `program` с собственным `id`
- `programs/{program_id}/schedule` для модуля возвращает `lessons[]` с `lesson_items[]`
- `programs/{profession_id}/schedule` для верхнеуровневой программы возвращает пустые `lessons`

---

## Статистика по lesson_items

Исследованы 2 программы, получены данные по 23 модулям бакалавриата и 5 модулям курса SQL/Power BI.

| Тип | Количество | Доля |
|-----|-----------|------|
| **video** | 492 | 29.3% |
| **attachment** | 389 | 23.2% |
| **webinar** | 377 | 22.5% |
| **text** | 152 | 9.1% |
| **task** | 129 | 7.7% |
| **test** | 93 | 5.5% |
| **poll** | 29 | 1.7% |
| **longread** | 12 | 0.7% |
| **goals_poll** | 2 | 0.1% |
| **quiz** | 2 | 0.1% |
| **Итого** | **1677** | **100%** |

---

## Типы lesson_items: структура и извлечение

### 1. `video` — записанные видеолекции

**Структура ответа `lesson_items/{id}`:**
```json
{
  "id": 3130820,
  "type": "video",
  "title": "Определения и основные понятия",
  "video_url": "https://kinescope.io/tQh7UAcuDDQAboyHfQwC5c",
  "passed_rule": "video_view_X",
  "passed_value": 80,
  "approximate_progress_time": 10,
  ...
}
```

**Извлечение контента:**
1. Берём `video_url` → извлекаем ID: `tQh7UAcuDDQAboyHfQwC5c`
2. Запрашиваем `GET https://kinescope.io/embed/{video_id}`
3. Парсим HTML, ищем `var playerOptions = {...};`
4. Извлекаем `playlist[0].sources.hls.src` — master.m3u8

**Результат:**
```
https://kinescope.io/{video_uuid}/master.m3u8
```

**Полученные поля из Kinescope:**
| Поле | Описание |
|------|----------|
| `hls_src` | master.m3u8 (HLS playlist) |
| `poster` | URL превью (JPEG) |
| `title` | Название видео |
| `duration` | Длительность в секундах |
| `qualities` | Доступные качества: 360, 480, 720, 1080 |

**Формат master.m3u8:**
```
#EXTM3U
#EXT-X-STREAM-INF:...,RESOLUTION=1920x1080
media.m3u8?quality=1080&type=video
#EXT-X-STREAM-INF:...,RESOLUTION=1280x720
media.m3u8?quality=720&type=video
...
```

**Примечание:** Kinescope НЕ предоставляет прямых MP4-ссылок в `playerOptions`. Только HLS (сегментированный поток). Для получения MP4 требуется:
- `ffmpeg -i master.m3u8 -c copy output.mp4`
- или yt-dlp с HLS URL

---

### 2. `webinar` — записи вебинаров

**Структура** аналогична `video`, плюс дополнительные поля:
```json
{
  "type": "webinar",
  "starts_at": "2026-02-17T15:55:00.000Z",
  "ends_at": "2026-02-17T17:25:00.000Z",
  "experts": [{"id": ..., "full_name": "...", "avatar_path": "..."}],
  "video_url": "https://kinescope.io/...",
  "webinar_url": "",
  "youtube_video_id": null,
  "translation_adapter": "webinar_ru_native"
}
```

**Извлечение:** Тот же алгоритм, что и для `video` — `video_url` → Kinescope embed → HLS.

---

### 3. `attachment` — прикреплённые файлы

**Структура:**
```json
{
  "type": "attachment",
  "title": "Рабочая программа дисциплины",
  "files": [
    {
      "id": 77664,
      "name": "Рабочая программа дисциплины",
      "link": "https://u.netology.ru/backend/uploads/lms/attachments/files/data/77664/....pdf",
      "extension": "pdf",
      "size": "958,7 КБ"
    }
  ]
}
```

**Извлечение:** Прямые ссылки на файлы уже есть в ответе. Ссылки вида `https://u.netology.ru/backend/uploads/...` — публичные, не требуют авторизации.

---

### 4. `text` — текстовые материалы

**Структура:**
```json
{
  "type": "text",
  "title": "Критерии оценивания",
  "content": "**Критерии оценивания**\n\n* Домашнее творческое задание...",
  "content_type": "markdown"
}
```

**Извлечение:** Поле `content` содержит текст в формате Markdown. Достаточно сохранить как `.md`.

---

### 5. `longread` — структурированные статьи

**Структура:**
```json
{
  "type": "longread",
  "title": "...",
  "content": {
    "version": 1,
    "elements": [
      {
        "id": "...",
        "type": "list",
        "items": [
          {"id": "...", "value": "<p>HTML-контент</p>"}
        ]
      },
      {
        "id": "...",
        "type": "paragraph",
        "value": "<p>Текст</p>"
      }
    ]
  }
}
```

**Извлечение:** `content` — JSON с элементами. Каждый элемент имеет `type`:
- `list` → список с `items[].value` (HTML)
- `paragraph` → `value` (HTML)
- `image` → возможно, изображения

Для конвертации в Markdown/HTML нужен парсер этого формата.

---

### 6. `task` — задания

**Структура:**
```json
{
  "type": "task",
  "title": "Паспорт компетенций — Дедлайн 01.04",
  "content": "Текст задания...",
  "passed_rule": "task_solution"
}
```

**Извлечение:** Поле `content` содержит текст задания. Формат — Markdown или HTML.

---

### 7. `test` — тесты

**Структура:**
```json
{
  "type": "test",
  "title": "Тест по теме 1 «Комбинаторика»",
  "questions_count": 3,
  "duration": 0,
  "lesson_test": {
    "id": 73324,
    "max_solutions_count": 2,
    "percent_to_pass": 70,
    "user_test": {...}
  },
  "last_solution": {...}
}
```

**Извлечение:** В `lesson_items/{id}` тесты содержат только **метаданные** (количество вопросов, порог прохождения). Сами вопросы и ответы **НЕ возвращаются**. Вероятно, они доступны через отдельный endpoint (возможно, `lesson_tests/{id}` или при прохождении теста).

---

### 8. `poll` — опросы

**Структура:** аналогична `test`, но с `type: "poll"`. Содержит метаданные, но не сами вопросы в ответе `lesson_items/{id}`.

---

### 9. `quiz` — квизы

**Структура:** аналогична `test`. Также без вопросов в ответе.

---

### 10. `goals_poll` — целевые опросы

Найдено 2 штуки. Один вернул 404, другой — пустой `text` без контента.

---

## Извлечение видео из Kinescope: пошаговый алгоритм

### Шаг 1: Получить video_url из lesson_items/{id}
```python
video_url = lesson_item["video_url"]  # https://kinescope.io/{id}
```

### Шаг 2: Запросить embed-страницу
```python
import httpx, re
resp = httpx.get(f"https://kinescope.io/embed/{video_id}", headers={
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://netology.ru/"
})
```

### Шаг 3: Парсинг playerOptions
```python
match = re.search(r'var playerOptions = ({.*?});', resp.text, re.DOTALL)
data = json.loads(match.group(1))
hls_url = data["playlist"][0]["sources"]["hls"]["src"]
# → https://kinescope.io/{uuid}/master.m3u8
```

### Шаг 4: Получение качеств
```python
resp = httpx.get(hls_url)
# Парсим playlist, извлекаем варианты качества (360p, 480p, 720p, 1080p)
```

### Шаг 5: Скачивание видео
```bash
ffmpeg -headers "Referer: https://netology.ru/" -i "master.m3u8" -c copy output.mp4
```

---

## VTT-субтитры

**Результат:** Прямые URL для субтитров Kinescope **не найдены** через стандартные endpoint'ы:
- `/{video_id}/subtitles` → 404
- `/api/v1/videos/{id}/subtitles` → 404
- `/api/videos/{id}/subtitles` → 404

**Альтернативы:**
1. Субтитры могут быть встроены в HLS-поток (CMAF с субтитрами)
2. Возможно, нужен GraphQL-запрос к Kinescope с токеном
3. Playwright с перехватом `.vtt` запросов (как в `test_kinescope_vtt.py`)

---

## Результаты исследования

### ✅ Работает (контент извлекается без браузера)

| Тип | Способ извлечения | Сложность |
|-----|------------------|-----------|
| `video` | Kinescope embed → HLS master.m3u8 | Средняя |
| `webinar` | Kinescope embed → HLS master.m3u8 | Средняя |
| `attachment` | Прямая ссылка из `files[].link` | Простая |
| `text` | Поле `content` (Markdown) | Простая |
| `task` | Поле `content` (Markdown/HTML) | Простая |
| `longread` | Поле `content` (structured JSON → HTML) | Средняя |

### ⚠️ Частично работает

| Тип | Проблема |
|-----|----------|
| `test` | Только метаданные, без вопросов/ответов |
| `poll` | Только метаданные |
| `quiz` | Только метаданные |
| `goals_poll` | 404 или пустой контент |

### ❌ Требует Playwright/дополнительного исследования

| Задача | Причина |
|--------|---------|
| VTT-субтитры | Не найден API endpoint |
| Конвертация HLS → MP4 | Требует ffmpeg/yt-dlp |
| Парсинг longread JSON | Нужен конвертер в Markdown |
| Вопросы тестов | Нет в lesson_items/{id} |

---

## Файлы исследования

**Скрипты:** `backend/tests/lesson_item_research/`
- `01_explore_lesson_items.py` — первичное исследование
- `02_fetch_lesson_items_detailed.py` — обход profession/modules
- `03_fetch_all_programs.py` — полный обход всех программ
- `04_explore_kinescope.py` — исследование Kinescope API
- `05_extract_media_urls.py` — извлечение прямых URL

**Данные:** `backend/api_tests_etc/lesson_items/`
- `01_calendar_filters.json` — список программ
- `02_program_*_schedule.json` / `02_profession_*_schedule.json` — schedules
- `03_all_lesson_items_summary.json` — 1677 lesson_items
- `04_lesson_item_{id}_{type}.json` — детальные ответы (44 шт.)
- `05_all_detailed.json` — агрегированные детальные ответы
- `06_extracted_media_urls.json` — извлечённые медиа-URL
- `kinescope_*.json` — результаты исследования Kinescope

---

## Следующие шаги

1. **Реализовать модуль `backend/services/content_extractor/`**
   - Класс `KinescopeExtractor` — embed → HLS → ffmpeg
   - Класс `AttachmentDownloader` — прямые ссылки
   - Класс `TextExtractor` — markdown/content
   - Класс `LongreadConverter` — structured JSON → Markdown

2. **Исследовать endpoint'ы для тестов**
   - `GET /backend/api/user/lesson_tests/{id}` — возможно, там вопросы
   - Или тесты загружаются динамически при открытии

3. **VTT-субтитры**
   - Проверить GraphQL Kinescope с авторизацией
   - Или использовать Playwright как fallback для субтитров

4. **HLS → MP4**
   - Интегрировать ffmpeg или yt-dlp в пайплайн
   - Сохранять видео с выбором качества

5. **Структурированный longread**
   - Написать парсер elements → Markdown
   - Поддержка списков, параграфов, изображений, ссылок
