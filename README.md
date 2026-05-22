# 🎓 StudyCore

> Ассистент для студентов Нетологии.

---

## Что это

StudyCore — это инструмент, который:

1. **Заходит** в личный кабинет Нетологии от твоего имени
2. **Собирает** материалы курсов (видео, PDF, презентации, VTT-субтитры)
3. **Генерирует** качественные конспекты с помощью LLM (DeepSeek V3.2)
4. **Сохраняет** всё в структурированном виде (Notion / Second Brain)

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/golyshevventure/study_automatization.git
cd study_automatization

# 2. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Установить Playwright
playwright install chromium

# 5. Создать .env
cp .env.example .env
# Отредактировать .env — вписать логин/пароль от Нетологии и OpenRouter API ключ

# 6. Запустить один курс
python run_agent.py bhebfad-25-memeo-2

# 7. Запустить весь бакалавриат
python run_all_bachelor.py
```

## Технологии

| Компонент | Технология |
|-----------|------------|
| Скрейпинг | Playwright (headless/visible) |
| LLM | DeepSeek V3.2 via OpenRouter |
| Транскрибация | Whisper (локально, GPU) |
| Хранение | Notion API / Markdown файлы |
| Конфиг | python-dotenv |

## Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Нетология  │────▶│  Playwright │────▶│  VTT / PDF  │
│   (LMS)     │     │  (scraping) │     │   (контент) │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
┌─────────────┐     ┌─────────────┐            │
│  OpenRouter │◀────│  LLM (Deep │◀───────────┘
│    (API)    │     │   Seek V3)  │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  Конспекты  │────▶│   Notion    │
│   (.md)     │     │    (API)    │
└─────────────┘     └─────────────┘
```

## Структура проекта

```
Study_automatization/
├── run_agent.py              # Главный оркестратор
├── generate_summary.py        # LLM-генерация конспектов
├── pyproject.toml             # Конфиг pytest, black, isort
├── requirements.txt           # Зависимости
├── .env                       # Секреты (не коммитить!)
├── README.md                  # Этот файл
├── docs/
│   ├── TODO.md                # План разработки
│   ├── UNIT_ECONOMICS.md      # Финансовая модель
│   ├── KIMI.md                # Контекст для Kimi Code CLI
│   └── StudyCore.drawio       # Диаграмма архитектуры
├── src/
│   └── Скрейперы/
│       └── netology_scraper.py
├── Утилиты/
│   ├── material_classifier.py   # Классификация материалов
│   ├── conspect_writer.py       # Запись .md
│   ├── logger_config.py         # Логирование
│   └── ...
├── tests/
│   └── test_material_classifier.py
├── frontend/                   # Telegram Mini App (WIP)
└── output/                     # Логи прогонов
```

## Команды

```bash
# Запуск одной дисциплины
python run_agent.py <program_id>

# С перезаписью существующих файлов
python run_agent.py <program_id> --force

# Только конкретный предмет
python run_agent.py <program_id> --subject "Экономическая теория"

# Тесты
pytest tests/ -v

# Форматирование кода
black .

# Проверка стиля
flake8 .
```

## Roadmap

| Этап | Статус | Описание |
|------|--------|----------|
| v0.8.x | ✅ Готово | Генерация конспектов, скрейпинг, классификация |
| v0.9.0 | 🔄 В работе | Telegram Mini App, оптимизация скорости |
| v1.0 | 📋 Запланирован | Дедлайны, напоминания, бот |
| v1.1 | 📋 Запланирован | Сводки, интеграция с почтой |

## Переменные окружения (.env)

```bash
# Нетология
NETOLOGY_EMAIL=your@email.com
NETOLOGY_PASSWORD=your_password

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...

# Notion (опционально)
NOTION_TOKEN=secret_...
```

## Автор

**Никита** — студент Финансового университета

- GitHub: [@golyshevventure](https://github.com/golyshevventure)
- Email: golyshevventure@gmail.com

---

> ⚠️ **Важно:** `.env` и `Данные/netology_cookies.json` никогда не коммитьте в репозиторий!
