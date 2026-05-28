# Реструктуризация проекта: разделение backend и frontend

**Дата:** 2026-05-28
**Контекст:** Проект вырос из монолитной структуры с папками на кириллице (`Утилиты/`, `Тесты/`, `Данные/`) в полноценное приложение с React-фронтендом и Python-бэкендом. Требовалось привести структуру в соответствие с реальным использованием: отделить фронтенд (Vite + React + TS) от бэкенда (Python + Playwright + LLM), удалить мёртвый код и мусор, унифицировать пути.

---

## 1. Перемещения и переименования

### 1.1 `Утилиты/` → `backend/summary/summary_programs/`

**Что перемещено:**
| Файл | Назначение |
|------|-----------|
| `audio_extractor.py` | Извлечение аудио и VTT-субтитров |
| `conspect_writer.py` | Запись .md файлов в Second Brain |
| `local_whisper.py` | Локальная транскрибация Whisper (fallback) |
| `logger_config.py` | Конфигурация логирования |
| `material_classifier.py` | Классификация типа материала |
| `netology_api_client.py` | API-first клиент Netology |
| `netology_auth.py` | Авторизация через Playwright |
| `second_brain_cleanup.py` | Очистка Second Brain |
| `subject_index.py` | Индексные файлы предметов |

**Почему:** Папка `Утилиты/` на кириллице — проблема для WSL (путь часто ломается при копировании), плюс логически эти модули — часть пайплайна генерации конспектов, а не standalone утилиты. Новый путь отражает их роль как вспомогательных программ summary-пайплайна.

**Что удалено при переносе:**
- `transcription_queue.py` — не импортировался нигде (~180 строк очереди на SQLite). Содержал логику VTT-менеджмента, но очередь не использовалась.

---

### 1.2 `Тесты/` + `tests/` → `backend/tests/`

**Что перемещено:**
| Источник | Файлы |
|----------|-------|
| `Тесты/` | `check_auth.py`, `check_programs.py`, `explore_api.py`, `explore_structure.py`, `explore_structure_fast.py`, `find_disciplines.py`, `list_programs.py`, `test_api_endpoints.py`, `test_auth_and_disciplines.py` + 8 скриптов |
| `tests/` | `test_material_classifier.py` |

**Почему:** Дублирование — две папки с тестами (`Тесты/` и `tests/`). Обе на самом деле содержат standalone debug-скрипты, а не pytest-тесты. Унификация в одну папку внутри `backend/`.

---

### 1.3 `Данные/` → `backend/api_tests_etc/`

**Что перемещено:**
- `api_explore.json` — полный дамп API endpoint'ов (1.1 MB)
- `api_netology_ru_backend_api_*.json` — ~15 кэшированных ответов API
- `api_test_*.json` — тестовые дампы
- `netology_page.html`, `materials_page.json`, `program_schedule.json` — старые дампы

**Что удалено:**
- Устаревшие дампы (большинство `api_netology_*` файлов, `api_explore.json`)
- `agent.db` — мёртвая SQLite-база, не использовалась кодом

**Почему:** Папка `Данные/` на кириллице + хаос из кэшей, дампов и тестовых файлов. Переименование в `api_tests_etc/` отражает реальное содержимое: кэш ответов API и тестовые данные.

---

### 1.4 `data/` → `backend/netology_cookies/`

**Что перемещено:**
- `netology_cookies.json` — единственный нужный файл (cookies авторизации)

**Что удалено:**
- `data/audio/` — 962 MB WAV/MP4 аудио-файлов от старых прогонов
- `data/html_debug/` — 5 файлов debug HTML/PNG
- `data/debug_*.html` — 17 debug-дампов (~1.5 MB)
- `data/test_silence.wav` — тестовый аудио-файл

**Почему:** Папка `data/` была свалкой: cookies + 1 GB мусора. После внедрения VTT-экстракции аудио-fallback практически не используется. Cookies вынесены в отдельную папку, всё остальное — удалено.

---

### 1.5 `output/` → `backend/logs/`

**Старая структура:**
```
output/
├── logs/
│   ├── studycore.log      ← активный лог
│   └── errors.log         ← активный лог ошибок
└── archive/               ← 31 архивный лог
```

**Новая структура:**
```
backend/logs/
├── current/               ← активные логи (2 файла)
│   ├── studycore.log
│   └── errors.log
├── summaries/             ← логи генерации конспектов (20 файлов)
│   ├── run_full_sda_20260517.log
│   ├── run_mirovaya_20260517_*.log (9 шт.)
│   ├── run_iya_20260518.log
│   ├── run_tv_20260518.log
│   ├── run_vvs_20260518.log
│   └── run_v[7-12].log
├── research/              ← исследовательские скрипты (6 файлов)
│   ├── explore_structure.log
│   ├── explore_structure_fast.log
│   ├── list_programs.log
│   ├── find_disciplines.log
│   ├── find_disciplines2.log
│   └── inspect_bachelor.log
└── tests/                 ← тестовые скрипты (7 файлов)
    ├── test_point_run_20260517.log
    ├── test_webinars_20260517.log
    ├── test_webinar_1205_vtt.log
    ├── run_test.log
    ├── run_test2.log
    ├── run_v7_test.log
    └── run_v7_test2.log
```

**Почему:** `output/` — слишком общее название. Логи — это бэкендовский артефакт, им не место в корне проекта. Разделение по категориям позволяет быстро находить нужную историю.

**Обновления при переносе:**
- `backend/summary/summary_programs/logger_config.py` — путь изменён с `output/logs` на `backend/logs/current`
- `.gitignore` — `output/` заменён на `backend/logs/current/` (текущие логи не коммитятся, архивные оставлены в git как история)

---

### 1.6 `Промпты/system.txt` → `backend/summary/prompt_for_deepsek_v3.2/system.txt`

**Почему:** Промпт — часть пайплайна генерации конспектов (`generate_summary.py` загружает его оттуда). Логично хранить рядом с кодом, который его использует, а не в отдельной папке на кириллице.

---

### 1.7 `src/` → удалён

**Что было внутри:**
- `src/Генераторы/` — пустая папка (только `__init__.py`)
- `src/Хранилище/` — пустая папка (только `__init__.py`)
- `src/Скрейперы/` — содержал `netology_scraper.py`, но он переехал в `backend/summary/`

**Почему:** `src/` — артефакт ранней структуры. Все используемые файлы из неё перенесены в `backend/`, пустые папки — удалены.

---

## 2. Удалённые файлы и папки

| Файл/папка | Размер | Причина удаления |
|------------|--------|-----------------|
| `data/audio/` | 962 MB | Временные аудио-файлы, VTT-экстракция заменила их |
| `data/debug_*.html` (17 шт.) | ~1.5 MB | Debug-дампы отладки авторизации и скрапинга |
| `data/html_debug/` | 5 файлов | Артефакты исследования структуры |
| `data/test_silence.wav` | 192 KB | Тестовый аудио-файл |
| `agent.db` | ~100 KB | Мёртвая SQLite, не импортировалась нигде |
| `database.py` | ~100 строк | Не импортировалась нигде, SQLite-схема без использования |
| `docs/TODO.md` | 33 KB | Дубль корневого `TODO.md` |
| `src/Генераторы/` | 0 байт | Пустая зарезервированная папка |
| `src/Хранилище/` | 0 байт | Пустая зарезервированная папка |
| `Утилиты/transcription_queue.py` | ~180 строк | Не импортировался, мёртвый код |

---

## 3. Обновления конфигурации

### 3.1 `.gitignore`

**Добавлено:**
- `backend/logs/current/` — текущие логи не коммитятся
- `__pycache__/` — Python кэш
- `.pytest_cache/` — pytest кэш
- `.venv/` — виртуальное окружение
- `*.wav`, `*.mp4` — аудио/видео файлы
- `push.sh` — скрипт push

**Удалено:**
- `output/` — папка больше не существует

### 3.2 `requirements.txt`

**Добавлено:**
- `httpx>=0.25.0` — используется в `netology_api_client.py`
- `torch>=2.0.0` — используется в `local_whisper.py`
- `transformers>=4.30.0` — используется в `local_whisper.py`

**Убрано:**
- `black`, `flake8`, `isort`, `pytest` — dev-зависимости

### 3.3 `logger_config.py`

```python
# Было:
LOG_DIR = Path(__file__).parent.parent / "output" / "logs"

# Стало:
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "current"
```

---

## 4. Итоговая структура проекта

```
Study_automatization/
├── backend/
│   ├── summary/
│   │   ├── run_agent.py                    # Главный оркестратор
│   │   ├── generate_summary.py             # LLM-генерация
│   │   ├── netology_scraper.py             # Playwright scraper (legacy-режим)
│   │   └── prompt_for_deepsek_v3.2/
│   │       └── system.txt                  # Промпт для DeepSeek
│   ├── summary_programs/                   # Бывшие "Утилиты"
│   │   ├── audio_extractor.py
│   │   ├── conspect_writer.py
│   │   ├── local_whisper.py
│   │   ├── logger_config.py
│   │   ├── material_classifier.py
│   │   ├── netology_api_client.py
│   │   ├── netology_auth.py
│   │   ├── second_brain_cleanup.py
│   │   └── subject_index.py
│   ├── tests/                              # Бывшие "Тесты/" + "tests/"
│   │   ├── check_auth.py
│   │   ├── check_programs.py
│   │   ├── explore_api.py
│   │   ├── explore_structure.py
│   │   ├── find_disciplines.py
│   │   ├── list_programs.py
│   │   ├── test_api_endpoints.py
│   │   └── ... (+ 8 скриптов)
│   ├── api_tests_etc/                      # Бывшие "Данные/"
│   │   └── api_test_*.json (тестовые дампы)
│   ├── netology_cookies/                   # Бывшие "data/"
│   │   └── netology_cookies.json
│   └── logs/
│       ├── current/                        # Активные логи
│       ├── summaries/                      # История прогонов
│       ├── research/                       # Исследовательские логи
│       └── tests/                          # Тестовые логи
├── frontend/                               # Vite + React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── data/
│   │   ├── utils/
│   │   └── types/
│   └── ...
├── reports/                                # Markdown-отчёты
├── kimi/                                   # Документация (TODO, KIMI)
├── docs/                                   # Доп. документация
├── .env
├── .gitignore
├── README.md
├── TODO.md
├── requirements.txt
└── pyproject.toml
```

---

## 5. Итог

| Метрика | Значение |
|---------|----------|
| Освобождено на диске | ~965 MB |
| Перемещено папок | 5 (`Утилиты`, `Тесты`, `Данные`, `data`, `Промпты`) |
| Удалено мёртвого кода | 4 файла + 3 пустые папки |
| Перемещено логов | 35 файлов → 4 категории |
| Унифицировано имён | 0 папок на кириллице в корне |

**Результат:**
- Проект разделён на чёткие домены: `backend/` (Python) и `frontend/` (React)
- Все кириллические папки убраны из корня (решена проблема WSL)
- Логи структурированы и доступны для анализа
- Мёртвый код и мусор удалены
- `.gitignore` актуализирован
