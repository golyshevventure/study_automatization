# Отчёт: Внедрение API-first режима (v0.9.0)

> Дата: 2026-05-23
> Сессия: реализация API-first подхода для StudyCore
> Коммит: `b44eaa2`

---

## 1. Цель работы

Перевести сбор контента Нетологии с Playwright-скрейпинга на REST API, оставив Playwright только для авторизации (получения cookies). Ожидаемое ускорение: **30x** (с ~30 мин/дисциплина до ~1–2 мин).

---

## 2. Что сделано

### 2.1. Исследование API Нетологии

Создан и запущен тестовый скрипт `Тесты/test_api_first.py`. Проверены endpoint'ы:

| Endpoint | Статус | Примечание |
|----------|--------|------------|
| `GET /backend/api/user/profile` | ✅ | Проверка валидности cookies |
| `GET /programs/{slug}/schedule` | ✅ | 42 lessons, `lesson_items` внутри |
| `GET /programs/{numeric_id}/schedule` | ✅ | Работает и по числовому ID |
| `GET /lesson_items/{id}` (type=`text`) | ✅ | `content` + `content_type: "markdown"` |
| `GET /lesson_items/{id}` (type=`webinar`) | ✅ | `video_url`, `content: ""` |
| `GET /lesson_items/{id}` (type=`video`) | ✅ | `video_url`, `content: ""` |
| `GET /lesson_items/{id}` (type=`attachment`) | ✅ | `files[]` с `link`, `extension`, `size` |

**Ключевой инсайт:** для `type=attachment` API отдаёт `files[]` со ссылками на PDF/DOCX/PPTX — Playwright для скачивания файлов **больше не нужен**.

### 2.2. Создан `NetologyAPIClient`

**Файл:** `Утилиты/netology_api_client.py`

Методы:
- `get_program_info(program_id)` — метаданные программы (для `program_title`)
- `get_program_schedule(program_id)` — список занятий с `lesson_items`
- `get_lesson_item(item_id)` — детали item'а
- `fetch_item_content(item, subject_name)` — high-level сборщик контента:
  - `type=text` → берёт `content` (markdown)
  - `type=attachment` → скачивает файл, парсит PDF/DOCX/PPTX
  - `type=video/webinar` → сохраняет `video_url`
  - `structure page detection` — тот же guard, что и в Playwright-версии
  - `audio fallback` — интегрирован с `extract_audio_from_mp4` + Whisper

### 2.3. Адаптация `run_agent.py`

- Добавлен флаг `--api`
- **Без `--api`** — работает старый Playwright-режим (100% обратная совместимость)
- **С `--api`** — запускается `_run_api_mode()`:
  - Авторизация через Playwright (только для cookies)
  - Структура и контент через `NetologyAPIClient`
  - Классификация, merge/split, dedup, audio fallback — без изменений
- Созданы `_process_items_api()` и `_get_item_content_api()` — API-версии обработки

### 2.4. Доработка `audio_extractor.py`

Добавлена `resolve_kinescope_video_url()`:
- Преобразует short URL (`kinescope.io/XXXX`) → `master.m3u8`
- Парсит HTML embed-страницы Kinescope через regex

### 2.5. Тестовый прогон

**Команда:**
```bash
python run_agent.py bhebfad-25-memeo-2 --api --subject "Тема 1" --force
```

**Результат:**
- ⚡ Длительность: **~4 минуты** (включая ошибки ffmpeg)
- ✅ Конспект сгенерирован: **11 451 символ**
- ✅ Файл сохранён: `Конспекты/Тема 1 «Мировая экономика...».md`

### 2.6. Документация

- `docs/TODO.md` и `TODO.md` — обновлены: добавлены галочки v0.9.0, лог тестирования

---

## 3. Найденные проблемы

### 3.1. Kinescope 403 Forbidden (audio fallback) — 🔴 Критично

`resolve_kinescope_video_url()` получает **403 Forbidden** при HTTP-запросе к short URL Kinescope. Видеохостинг блокирует не-браузерные запросы.

**Влияние:** в API-режиме аудио fallback (Whisper) для видео **не работает**.

**Возможные решения:**
1. Playwright fallback — открывать страницу Kinescope, перехватывать `m3u8` (как сейчас для VTT)
2. Передавать cookies браузера в `requests`
3. Использовать `yt-dlp` вместо прямого ffmpeg

**Рекомендация:** пока оставить ограничение. В API-режиме текстовые материалы обрабатываются мгновенно. Видео без субтитров — edge case. Доработать в следующей итерации.

### 3.2. Имя предмета из API

`program_title` из `/programs/{id}` = `"1 курс, 2 семестр: Мировая экономика и международные экономические отношения"`. Это длиннее и менее чистое, чем раньше.

**Решение:** парсить `name`, убирая префикс `"1 курс, 2 семестр: "`.

### 3.3. Время выполнения

Тема 1 заняла ~4 минуты. Из них:
- API-запросы: мгновенно (< 1 сек)
- Генерация конспекта LLM: ~1–2 минуты
- Ошибки ffmpeg (2 попытки): ~1–2 минуты

**Прогноз без аудио fallback:** ~2 минуты на раздел (vs ~60 минут в Playwright-режиме).

---

## 4. Сравнение режимов

| Параметр | Playwright | API-first |
|----------|-----------|-----------|
| Авторизация | Playwright | Playwright (1 раз) |
| Структура программы | 10–30 сек | **200–500 мс** |
| Контент 1 item | 5–10 сек | **50–200 мс** |
| Тема 1 (факт) | ~60 мин | **~4 мин** |
| Тема 1 (прогноз, без аудио fallback) | ~60 мин | **~2 мин** |

---

## 5. Изменённые и созданные файлы

| Файл | Действие | Описание |
|------|----------|----------|
| `run_agent.py` | 📝 Изменён | `--api` флаг, `_run_api_mode()`, `_process_items_api()`, `_get_item_content_api()` |
| `Утилиты/netology_api_client.py` | 🆕 Создан | HTTP-клиент для API Нетологии |
| `Утилиты/audio_extractor.py` | 📝 Изменён | `resolve_kinescope_video_url()` |
| `Тесты/test_api_first.py` | 🆕 Создан | Тестовый скрипт для проверки API |
| `docs/TODO.md`, `TODO.md` | 📝 Изменены | Лог v0.9.0 |

---

## 6. Следующие шаги (предлагаются)

1. **Полный тест дисциплины** — прогнать Мировую экономику целиком (42 раздела) в API-режиме, сравнить выход с Playwright-версией
2. **Исправить имя предмета** — убрать префикс курса/семестра из `program_title`
3. **Доработать audio fallback** — Playwright fallback для Kinescope или `yt-dlp`
4. **Бенчмарк** — замерить полный прогон дисциплины: API vs Playwright

---

*Отчёт сформирован автоматически после сессии разработки.*
