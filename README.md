# 🎓 StudyCore

> Ассистент для студентов Нетологии. Генерация конспектов, отслеживание дедлайнов, структурирование учебных материалов.

---

## Что это

StudyCore — полнофункциональное приложение для автоматизации учёбы в Нетологии:

1. **Авторизация** — заходит в личный кабинет от вашего имени (Playwright + cookies)
2. **Сбор материалов** — получает расписание, дисциплины и задания через API Netology
3. **Генерация конспектов** — извлекает контент (PDF, PPTX, VTT-субтитры) и создаёт качественные конспекты через LLM (DeepSeek V3.2 via OpenRouter)
4. **Дедлайны** — отображает актуальные дедлайны по всем программам с фильтрами и сортировкой
5. **Second Brain** — сохраняет конспекты в структурированном виде (Markdown)

---

## Технологии

### Backend

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.12+ |
| Скрейпинг / Auth | Playwright (headless/visible) |
| HTTP клиент | `httpx` + `requests` |
| LLM | DeepSeek V3.2 via OpenRouter API |
| Транскрибация (fallback) | Whisper (локально, `torch` + `transformers`) |
| HTML парсинг | `beautifulsoup4` + `lxml` |
| Конфиг | `python-dotenv` |
| Форматирование | `black` + `isort` |
| Тестирование | `pytest` |

### Frontend

| Компонент | Технология |
|-----------|------------|
| Бандлер | Vite 8 |
| Фреймворк | React 19 |
| Язык | TypeScript 6 |
| Стили | Tailwind CSS 3.4 |
| Иконки | Lucide React |
| Роутинг | React Router DOM 7 |
| UI компоненты | shadcn/ui |

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React + TypeScript + Tailwind + Vite                       │
│  localhost:5173                                             │
│                                                             │
│  • Home — дашборд (курсы, дедлайны, заметки)               │
│  • Deadlines — все дедлайны с фильтрами                    │
│  • Notes — список конспектов                               │
│  • NoteDetail — просмотр конспекта                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ (пока без API — статические данные)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  Python + Playwright + LLM                                   │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Netology   │───▶│ API Client  │───▶│  Content    │     │
│  │   (LMS)     │    │  (httpx)    │    │  (VTT/PDF)  │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                                 │           │
│  ┌─────────────┐    ┌─────────────┐            │           │
│  │  OpenRouter │◀───│ LLM (Deep   │◀───────────┘           │
│  │    (API)    │    │ Seek V3.2)  │                        │
│  └──────┬──────┘    └─────────────┘                        │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │  Конспекты  │───▶│ Second Brain│                        │
│  │   (.md)     │    │  (Markdown) │                        │
│  └─────────────┘    └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура проекта

```
Study_automatization/
├── backend/                          # Python backend
│   ├── summary/                      # Основной пайплайн
│   │   ├── run_agent.py              # Главный оркестратор (ETL)
│   │   ├── generate_summary.py       # LLM-генерация конспектов
│   │   ├── netology_scraper.py       # Playwright scraper (legacy-режим)
│   │   └── prompt_for_deepsek_v3.2/
│   │       └── system.txt            # Системный промпт для LLM
│   ├── summary_programs/             # Вспомогательные модули
│   │   ├── audio_extractor.py        # Извлечение аудио/VTT
│   │   ├── conspect_writer.py        # Запись .md файлов
│   │   ├── local_whisper.py          # Локальная транскрибация
│   │   ├── logger_config.py          # Логирование
│   │   ├── material_classifier.py    # Классификация материалов
│   │   ├── netology_api_client.py    # API-first клиент Netology
│   │   ├── netology_auth.py          # Авторизация через браузер
│   │   ├── second_brain_cleanup.py   # Очистка Second Brain
│   │   └── subject_index.py          # Индекс предметов
│   ├── tests/                        # Тестовые и debug-скрипты
│   │   ├── check_auth.py
│   │   ├── explore_structure.py
│   │   ├── find_disciplines.py
│   │   ├── list_programs.py
│   │   └── ... (+ 14 скриптов)
│   ├── api_tests_etc/                # Кэш API-ответов (JSON)
│   ├── netology_cookies/             # Cookies авторизации
│   │   └── netology_cookies.json
│   └── logs/                         # Логи
│       ├── current/                  # Активные логи (не в git)
│       ├── summaries/                # История прогонов run_agent
│       ├── research/                 # Исследовательские логи
│       └── tests/                    # Тестовые логи
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/               # UI компоненты
│   │   ├── pages/                    # Страницы (Home, Deadlines, Notes)
│   │   ├── hooks/                    # React hooks
│   │   ├── data/                     # Статические данные
│   │   ├── utils/                    # Утилиты
│   │   └── types/                    # TypeScript типы
│   ├── public/
│   └── package.json
├── reports/                          # Markdown отчёты по датам
├── kimi/                             # Документация для Kimi CLI
├── .env                              # Секреты (НЕ КОММИТИТЬ!)
├── .env.example                      # Шаблон .env
├── requirements.txt                  # Python зависимости
├── pyproject.toml                    # Конфиг black/isort/pytest
└── README.md                         # Этот файл
```

---

## Локальное развёртывание

### Требования

- Python 3.12+
- Node.js 20+
- Git

### 1. Клонировать репозиторий

```bash
git clone https://github.com/golyshevventure/study_automatization.git
cd study_automatization
```

### 2. Настроить backend

```bash
# Создать виртуальное окружение
python -m venv .venv

# Активировать (Linux/Mac)
source .venv/bin/activate
# Или Windows:
# .venv\Scripts\activate

# Установить Python-зависимости
pip install -r requirements.txt

# Установить браузер для Playwright
playwright install chromium
```

### 3. Настроить переменные окружения

```bash
cp .env.example .env
# Отредактируй .env — вставь свои данные
```

Содержимое `.env`:

```bash
# Нетология (обязательно)
NETOLOGY_EMAIL=your@email.com
NETOLOGY_PASSWORD=your_password

# OpenRouter (обязательно для генерации конспектов)
OPENROUTER_API_KEY=sk-or-v1-...

# GitHub (опционально)
GITHUB_TOKEN=ghp_...
```

### 4. Настроить frontend

```bash
cd frontend

# Установить npm-зависимости
npm install

# Запустить dev-сервер
npm run dev
```

Фронтенд откроется на `http://localhost:5173`.

### 5. Запуск

**Генерация конспектов (backend):**

```bash
# Активировать venv
source .venv/bin/activate

# Запустить одну программу
cd backend/summary
python run_agent.py <program_id>

# Примеры:
python run_agent.py bhebfad-25-memeo-2
python run_agent.py bhebfad-25-fil-2 --force
python run_agent.py bhebfad-25 --subject "Экономическая теория"
```

**Просмотр дедлайнов (frontend):**

```bash
cd frontend
npm run dev
# Открыть http://localhost:5173
```

---

## Команды

### Backend

```bash
# Генерация конспектов для программы
python backend/summary/run_agent.py <program_id>

# С перезаписью существующих
python backend/summary/run_agent.py <program_id> --force

# Только конкретный предмет
python backend/summary/run_agent.py <program_id> --subject "Название"

# Запуск тестов
pytest backend/tests/ -v

# Форматирование кода
black backend/
isort backend/
```

### Frontend

```bash
cd frontend

# Dev-сервер с HMR
npm run dev

# Production сборка
npm run build

# Превью production сборки
npm run preview

# Линтинг
npm run lint
```

---

## Roadmap

| Этап | Статус | Описание |
|------|--------|----------|
| v0.8.x | ✅ Готово | Генерация конспектов, скрейпинг, классификация |
| v0.9.0 | ✅ Готово | Реакт-фронтенд (Vite + TS + Tailwind), дедлайны |
| v0.9.5 | 🔄 В работе | Интеграция фронтенда с live API (реальные данные вместо кэша) |
| v1.0 | 📋 Запланирован | Бэкенд-API для фронтенда, авторизация, polling дедлайнов |
| v1.1 | 📋 Запланирован | Телеграм-бот, push-уведомления |
| v1.2 | 📋 Запланирован | AI-ассистент для ответов на вопросы по материалам |

---

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|-------------|----------|
| `NETOLOGY_EMAIL` | ✅ | Email от аккаунта Нетологии |
| `NETOLOGY_PASSWORD` | ✅ | Пароль от аккаунта Нетологии |
| `OPENROUTER_API_KEY` | ✅ | API ключ OpenRouter (для LLM) |
| `GITHUB_TOKEN` | ❌ | Токен GitHub (для backup) |

---

## Логи

Логи хранятся в `backend/logs/`:

| Папка | Содержимое | В git? |
|-------|-----------|--------|
| `current/` | Активные логи (`studycore.log`, `errors.log`) | ❌ Нет |
| `summaries/` | История прогонов `run_agent.py` | ✅ Да |
| `research/` | Логи исследовательских скриптов | ✅ Да |
| `tests/` | Логи тестовых запусков | ✅ Да |

---

## Автор

**Никита** — студент Финансового университета

- GitHub: [@golyshevventure](https://github.com/golyshevventure)
- Email: golyshevventure@gmail.com

---

> ⚠️ **Важно:** `.env` и `backend/netology_cookies/netology_cookies.json` никогда не коммитьте в репозиторий! Эти файлы содержат персональные данные и API ключи.
