# Комплексный аудит StudyCore

**Дата аудита:** 2026-06-07  
**Версия проекта:** v0.9.3 (post-deadlines v1.2)  
**Коммит:** 26d2f00  
**Аудитор:** Kimi Code CLI (3 параллельных агента: backend, frontend, project structure)

---

## 📋 Содержание

1. [Executive Summary](#1-executive-summary)
2. [Backend Analysis](#2-backend-analysis)
3. [Frontend Analysis](#3-frontend-analysis)
4. [Project Structure & Documentation](#4-project-structure--documentation)
5. [User Experience (UX) Analysis](#5-user-experience-ux-analysis)
6. [Security Audit](#6-security-audit)
7. [Performance Analysis](#7-performance-analysis)
8. [Bug Report & Priorities](#8-bug-report--priorities)
9. [MVP Assessment](#9-mvp-assessment)
10. [Roadmap & Recommendations](#10-roadmap--recommendations)

---

## 1. Executive Summary

StudyCore — это fullstack-приложение для автоматизации работы с образовательной платформой Netology. Проект вырос из скриптовой тулзы в полноценное приложение с FastAPI бэкендом, React фронтендом, PostgreSQL БД и JWT-авторизацией.

**Общая оценка: ~82% MVP**. Основные модули (авторизация, дедлайны, конспекты) функционально готовы. Критические проблемы сосредоточены в области:
- Безопасности (4 критические уязвимости)
- Документации и конфигурации (рассинхрон с кодом)
- Frontend stability (глотаются ошибки, десинхрон UI)
- Архитектуры (двойной Base, sync HTTP в async коде)

**Ключевые метрики:**

| Показатель | Значение |
|-----------|----------|
| Backend LOC | ~8,000 |
| Frontend LOC | ~6,500 |
| Тесты (pytest) | 16 (только merger) |
| Миграции Alembic | 1 активная (с багом) |
| GitHub milestones | 1 закрытый (v1.2) |
| Критических багов | 7 |
| Критических уязвимостей | 4 |
| Code smells | 10+ |

---

## 2. Backend Analysis

### 2.1 Критические проблемы

#### 🚨 Миграция падает на чистой БД
**Файл:** `backend/alembic/versions/4b42fea88b8e_add_deadline_events_and_sync_log.py`

Миграция пытается `DROP COLUMN deadlines_cached_at` и `deadlines_cache_json` из `user_sessions`, но эти колонки **никогда не создавались** в предыдущих миграциях. `alembic upgrade head` на чистой БД упадёт с `column "deadlines_cached_at" of relation "user_sessions" does not exist`.

**Влияние:** Невозможность развертывания проекта с нуля. Новый разработчик или CI/CD не смогут поднять БД.

**Решение:** Убрать `op.drop_column` из миграции или создать промежуточную миграцию.

---

#### 🚨 Утечка production credentials в git
**Файл:** `backend/alembic.ini`, строка 89

```ini
sqlalchemy.url = postgresql+asyncpg://studycore_admin_2026:StudyCore2026SecurePass@localhost:5432/studycore
```

Пароль и имя пользователя БД зафиксированы в VCS.

**Решение:** Использовать переменные окружения: `sqlalchemy.url = %(DATABASE_URL)s`.

---

#### 🚨 Синхронные HTTP-запросы блокируют event loop
**Файлы:** Все Netology-сервисы (`netology_auth.py`, `netology_calendar_service.py`, `netology_programs_service.py`, `netology_schedule_service.py`)

Все сервисы используют синхронный `httpx.Client(...)` внутри async endpoint'ов. Весь event loop блокируется на время ожидания ответа от Netology (до 60 сек).

**Последствия:** При одновременных запросах сервер перестаёт обрабатывать другие соединения. Один пользователь делает sync → все остальные ждут.

**Решение:** Переписать на `httpx.AsyncClient` с `async with`.

---

#### 🚨 Изменяемый дефолт в ORM-модели
**Файл:** `backend/models/deadline_event.py`, строка 105

```python
raw_items: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
```

`default=list` — классический Python-antipattern. SQLAlchemy 2.0 вызывает callable, но для JSONB рекомендуется `default=lambda: []`.

**Решение:** `default=lambda: []` или `default_factory=list` (если SQLAlchemy поддерживает).

---

#### 🚀 JWT-библиотека с известными CVE
**Файл:** `backend/core/security.py`

Используется `python-jose` (CVE-2024-33663, алгоритмическая путаница none/HS256).

**Решение:** Перейти на `PyJWT` или `authlib`.

---

#### 🚀 JWT payload содержит datetime объекты
**Файл:** `backend/core/security.py`, строки 25-30

```python
payload = {
    "sub": str(user_id),
    "iat": now,  # datetime object!
    "exp": now + timedelta(days=settings.JWT_EXPIRE_DAYS),  # datetime!
}
```

Стандарт JWT требует NumericDate (unix timestamp). `python-jose` может неправильно сериализовать datetime.

**Решение:** `.timestamp()` для всех datetime полей.

---

#### 🚀 Тесты работают с production БД
**Файл:** `backend/tests/test_session_service.py`, строка 17

Фикстура `db` использует `settings.DATABASE_URL` напрямую, без переключения на test database.

**Решение:** `TEST_DATABASE_URL` в `.env`, отдельная test БД, фикстура создаёт/удаляет таблицы.

---

### 2.2 Высокая серьёзность

| # | Проблема | Файл | Решение |
|---|----------|------|---------|
| 8 | Race condition при создании сессии (TOCTOU) | `session_manager.py:43-74` | `INSERT ... ON CONFLICT` |
| 9 | Неатомарная синхронизация дедлайнов | `deadline_service.py:49-95` | Транзакция `begin()` |
| 10 | Слабая контрольная сумма | `deadline_service.py:212-216` | SHA256 всего контента |
| 11 | Баг в фильтрации даты (мёртвый код) | `deadline_service.py:112-116` | Удалить `hour >= 0` |
| 12 | Баг в определении source в merger | `deadline_merger.py:134-141` | Исправить логику |
| 13 | Cookie с `secure=False` | `auth_router.py:95` | Конфиг `secure=True` |
| 14 | Дублирование `declarative_base()` | `models/base.py` + `core/database.py` | Один `Base` |
| 15 | Отсутствие шифрования cookies | `models/session.py:55-58` | Fernet encryption |
| 16 | IndexError в `NetologyProgramsService` | `netology_programs_service.py:74` | Проверка `None` |
| 17 | Нет валидации UUID в `event_id` | `deadlines_router.py:125` | `UUID` type |
| 18 | In-memory rate limiter | `programs_router.py:24` | Redis-based |
| 19 | `db.merge` в отдельной сессии | `programs_router.py:99-103` | Использовать одну сессию |
| 20 | `testpaths` указывает на корневую `tests/` | `pyproject.toml:19` | `backend/tests` |

---

### 2.3 Средняя серьёзность

- Нет проверки `expires_at` сессии в dependency
- `AuthRequest` без валидации (нет `EmailStr`)
- Утечка деталей ошибок клиенту (`detail=f"Внутренняя ошибка: {exc}"`)
- Хрупкая обработка ошибок Netology (проверка через `in`)
- Cookie name захардкожен в 5+ местах
- `get_db` без rollback при исключении
- N+1 запросов в `NetologyScheduleService`
- Нет rate limiting на `/deadlines/sync`

---

### 2.4 Code Smells

- `filter_type` валидируется вручную вместо `Literal`
- `DeadlineFilter` создан но не используется
- Дублирование `generate_uuid7()` в двух файлах
- Импорт внутри метода (`from sqlalchemy import func`)
- `now.time().hour >= 0` — мёртвый код
- `httpx.ReadTimeout` перехватывается, но `ConnectTimeout` — нет
- Тесты — исследовательские скрипты, не unit-тесты

---

## 3. Frontend Analysis

### 3.1 Критические баги

#### 🚨 Ошибки запроса полностью глотаются
**Файл:** `frontend/src/hooks/useDeadlines.ts`, строка 37-44

Из `useInfiniteQuery` не деструктуризируется `error`. Если запрос падает, пользователь видит «Нет предстоящих событий» вместо ошибки.

**Влияние:** Невозможно понять, что данные не загрузились.

**Решение:** Добавить `error` в return хука и отображать в UI.

---

#### 🚨 Десинхронизация счётчика уведомлений
**Файлы:** `BottomNav.tsx`, `Notifications.tsx`

`BottomNav` импортирует `notifications` из мок-файла `data.ts`. `Notifications` управляет локальным `useState`. При нажатии «Прочитать все» бейдж не обновляется.

**Решение:** Единый store (React Query или Context) для уведомлений.

---

#### 🚨 Хардкод API-URL по всему проекту
**Файлы:** `api/deadlines.ts`, `AuthContext.tsx`, `Welcome.tsx`, `usePrograms.ts`, `useCourse.ts`

`http://localhost:8000/api` захардкожен в 5+ файлах.

**Решение:** `VITE_API_BASE_URL` в `.env`.

---

#### 🚨 Замоканные сущности в «Конспектах»
**Файлы:** `Notes.tsx`, `NoteDetail.tsx`

Нажатие на любую заметку ведёт на `/notes/1`. Контент берётся из статического объекта `data.ts`.

**Решение:** Интеграция с live API.

---

#### 🚨 Фильтр по программе исчезает при пустой выборке
**Файл:** `Deadlines.tsx`

Если у выбранной программы нет событий для текущего фильтра, селект исчезает, но фильтр остаётся. Пользователь застревает.

**Решение:** Селект строить из всех программ пользователя, не только из загруженных событий.

---

#### 🚨 Таймштамп обновляется при неуспешной синхронизации
**Файл:** `Deadlines.tsx`

`doSilentSync` ловит ошибку в `catch` и не реджектит промис. UI показывает «Только что» даже при падении.

**Решение:** Реджектить промис при ошибке, обновлять `lastSync` только при успехе.

---

### 3.2 TypeScript проблемы

- Отсутствие импорта `React.ElementType` в `Deadlines.tsx`
- Неиспользуемая переменная в `catch` (`Welcome.tsx`)
- `@ts-nocheck` в `chart.tsx`

### 3.3 React проблемы

- Синхронный `setState` внутри `useEffect` (каскадные рендеры)
- Утечка памяти при размонтировании (`AuthContext`, `Deadlines`)
- IIFE в JSX без `useMemo` (`Home.tsx`)
- `Math.random()` во время рендера (`sidebar.tsx`)
- Нет `path="*"` в роутинге

### 3.4 Производительность

- `events` пересоздаётся на каждый рендер
- `programs` пересчитывается на каждый рендер
- `DeadlineCard` без `React.memo`
- Мёртвый `App.css`

### 3.5 UX проблемы

- Нет индикации фонового обновления
- Нет сообщения об ошибке загрузки
- Форсированный суффикс `МСК` (неправильный timezone)
- `new Date(year, month-1, day)` — timezone drift
- Нет плюрализации («1 вариантов»)
- Нет отличия просроченных событий
- FAB «Добавить конспект» — заглушка
- Кнопки «Редактировать/Поделиться» — заглушки

### 3.6 Accessibility

- Нет `<label>` у инпутов
- Нет `aria-live` для ошибок
- Кнопки фильтров без `aria-pressed`
- Навигация без `aria-current`
- Контрастность на грани

### 3.7 Мобильная адаптивность

- `MobileFrame` не адаптирован под реальные устройства
- Нет `viewport-fit=cover`
- Зависимость от внешних шрифтов Google
- Нет pull-to-refresh

---

## 4. Project Structure & Documentation

### 4.1 README.md — критический технический долг

| Проблема | Факт |
|----------|------|
| Структура проекта | Описывает `backend/summary_programs/`, но реально `backend/summary/summary_programs/` |
| Файлы в корне | Упоминает `database.py`, `run_agent.py` — удалены в v0.9.1 |
| CORS / порт | README: 5173, backend: 5174 |
| Документы в `docs/` | Упоминает удалённые файлы |
| TODO.md | Указывает на корень, актуальная версия в `kimi/TODO.md` |
| Roadmap | v0.9.5 «В работе», но по факту уже реализовано |

### 4.2 docs/DEDLINES_MODULE (опечатка: DEDLINES вместо DEADLINES)

- SPEC.md датирован 2026-06-23 (будущее)
- REPORT_FINAL.md указывает версию 1.1, хотя git — v1.2
- Устаревшие пункты («TS-ошибки», «авто-синхронизация»)

### 4.3 Конфигурация

| Файл | Проблема |
|------|----------|
| `.env.example` | Нет `DATABASE_URL`, `JWT_SECRET` |
| `pyproject.toml` | Нет `[project]`, `testpaths` указывает на корень |
| `requirements.txt` | Нет `uuid_utils`, `pydantic`, `sqlalchemy` |
| `alembic.ini` | Хардкод credentials |

### 4.4 Архитектурные проблемы

- Двойной `declarative_base()`
- `sys.path.insert` в скриптах
- Нет `docker-compose.yml`
- Нет CI/CD (GitHub Actions)

---

## 5. User Experience (UX) Analysis

### 5.1 Первый вход (Welcome → Home)

```
Welcome → ввод кредов → fetch localhost:8000 → authLogin() → checkAuth() → редирект
```

**Проблемы:**
- Лишний запрос `/auth/me` после успешного логина
- При offline — общая фраза «Ошибка авторизации», нет различия offline/500/неверные креды
- Нет `<label>` у полей — accessibility

### 5.2 Загрузка Home

```
usePrograms + useDeadlines("all", 3) → параллельно
```

**Проблемы:**
- Если `usePrograms` упадёт — ошибка
- Если `useDeadlines` упадёт — тихо пустой список
- Нет skeleton-заглушек, только CSS-спиннеры

### 5.3 Дедлайны

```
useInfiniteQuery → 20 событий
useEffect → doSilentSync (если lastSync > 5 мин)
```

**Проблемы:**
- Silent sync запускается даже если данные актуальны
- Нет индикации фонового обновления
- При ошибке — «Нет предстоящих событий» вместо ошибки
- Фильтр по программе исчезает при пустой выборке
- Таймштамп обновляется даже при неуспешной синхронизации

### 5.4 Конспекты (Notes)

**Проблемы:**
- Полностью замоканы — неработоспособны
- Навигация на `/notes/1` вне зависимости от ID
- FAB без действия
- Кнопки «Редактировать/Поделиться» без действия

### 5.5 Уведомления

**Проблемы:**
- Статические данные из `data.ts`
- «Прочитать все» не обновляет бейдж в BottomNav

### 5.6 Общие UX проблемы

| Проблема | Где |
|----------|-----|
| Нет Error Boundary | Любой Exception = белый экран |
| Нет offline-индикации | Нет `navigator.onLine` |
| Нет pull-to-refresh | Мобильные пользователи |
| Нет плюрализации | «1 вариантов» |
| Неверные даты | Timezone drift |
| Контрастность на грани | Accessibility |

---

## 6. Security Audit

### 6.1 Критические уязвимости

| # | Уязвимость | CVSS | Файл |
|---|-----------|------|------|
| 1 | Credentials leak в git (DB password) | ~7.5 | `alembic.ini` |
| 2 | `python-jose` CVE-2024-33663 | ~7.5 | `requirements.txt` |
| 3 | JWT cookie `secure=False` | ~6.5 | `auth_router.py` |
| 4 | Cookies в plaintext (no encryption) | ~6.0 | `models/session.py` |

### 6.2 Высокая серьёзность

- Нет rate limiting на `/deadlines/sync`
- Нет `HttpOnly` / `SameSite` для JWT cookie
- Нет `type` проверки в JWT payload
- `load_dotenv` при импорте — side effect

### 6.3 Средняя серьёзность

- `program` фильтр без wildcard escaping
- `CourseModule.link` без `HttpUrl` валидации
- Fallback `JWT_SECRET` захардкожен
- `__pycache__` в git

---

## 7. Performance Analysis

### 7.1 Backend

| Проблема | Влияние | Решение |
|----------|---------|---------|
| Sync HTTP в async | Блокировка event loop | `httpx.AsyncClient` |
| N+1 запросов к Netology | Медленный sync | `asyncio.gather` |
| In-memory rate limit | Не работает с uvicorn workers | Redis |
| Нет connection pooling | Не проверено | Настроить `pool_size` |

### 7.2 Frontend

| Проблема | Влияние | Решение |
|----------|---------|---------|
| `events` пересоздаётся | Лишние рендеры | `useMemo` |
| IIFE в JSX | Лишние вычисления | `useMemo` |
| `DeadlineCard` без memo | Лишние рендеры | `React.memo` |
| Зависимость от Google Fonts | FOUT / FOIT | Self-host fonts |

---

## 8. Bug Report & Priorities

### P0 (Критично — исправить немедленно)

| # | Баг | Компонент | Приоритет |
|---|-----|-----------|-----------|
| 1 | Миграция падает на чистой БД | Backend | 🔴 |
| 2 | Credentials leak в git | Backend | 🔴 |
| 3 | Sync HTTP блокирует event loop | Backend | 🔴 |
| 4 | Ошибки запроса глотаются | Frontend | 🔴 |
| 5 | Десинхрон уведомлений | Frontend | 🔴 |
| 6 | Хардкод API URL | Frontend | 🔴 |
| 7 | Конспекты неработоспособны | Frontend | 🔴 |
| 8 | Фильтр по программе застревает | Frontend | 🔴 |

### P1 (Высоко — исправить в ближайший спринт)

| # | Баг | Компонент |
|---|-----|-----------|
| 9 | Race condition при создании сессии | Backend |
| 10 | Неатомарная синхронизация | Backend |
| 11 | JWT datetime в payload | Backend |
| 12 | `python-jose` CVE | Backend |
| 13 | Cookie `secure=False` | Backend |
| 14 | Error Boundary отсутствует | Frontend |
| 15 | `setState` в эффектах | Frontend |
| 16 | Таймштамп при ошибке sync | Frontend |
| 17 | README устарел | Docs |
| 18 | `.env.example` неполный | Config |

### P2 (Средне — запланировать)

| # | Баг | Компонент |
|---|-----|-----------|
| 19 | N+1 запросов | Backend |
| 20 | In-memory rate limit | Backend |
| 21 | `testpaths` неверный | Config |
| 22 | Производительность (memo) | Frontend |
| 23 | Accessibility | Frontend |
| 24 | Мобильный viewport | Frontend |
| 25 | Двойной `Base` | Backend |

### P3 (Низко — по возможности)

| # | Баг | Компонент |
|---|-----|-----------|
| 26 | ESLint ошибки | Frontend |
| 27 | `App.css` мёртвый | Frontend |
| 28 | OpenAPI tags минимальны | Backend |
| 29 | Дублирование `generate_uuid7` | Backend |

---

## 9. MVP Assessment

**MVP определение:** Работающий бэкенд + фронтенд с авторизацией, дедлайнами и генерацией конспектов.

| Компонент | Вес | Прогресс | Оценка |
|-----------|-----|----------|--------|
| Бэкенд (API, БД, Auth) | 25% | 90% | ✅ |
| Генерация конспектов | 20% | 95% | ✅ |
| Дедлайны (full-stack) | 20% | 90% | ✅ |
| Фронтенд (UI, роутинг, интеграция) | 20% | 80% | ⚠️ |
| Документация / деплой | 10% | 30% | ❌ |
| Тесты | 5% | 40% | ❌ |

**Итого: ~82% MVP**

### Что реализовано ✅

- Авторизация (Netology + JWT + cookies)
- Сбор материалов (API-first)
- Генерация конспектов (LLM via OpenRouter)
- Second Brain (.md export)
- Дедлайны (бэкенд: merge, группировка, PostgreSQL)
- Дедлайны (фронтенд: фильтры, карточки, синхронизация, пагинация)
- Программы / прогресс

### Что не реализовано ❌

- Календарь (все события)
- Push-уведомления / Telegram
- AI-ассистент
- CI/CD
- Docker
- Live API для конспектов

---

## 10. Roadmap & Recommendations

### Немедленно (этот спринт — 1-2 дня)

1. **Исправить миграцию** — убрать `DROP COLUMN` или создать промежуточную
2. **Убрать credentials из `alembic.ini`** → env vars
3. **Исправить `useDeadlines.ts`** — вернуть `error` из `useInfiniteQuery`
4. **Вынести `API_BASE` в `.env`**
5. **Исправить `.env.example`** — добавить `DATABASE_URL`, `JWT_SECRET`
6. **Исправить README.md** — актуальная структура, запуск, переменные

### Ближайший спринт (1-2 недели)

7. **Переписать HTTP на async** (`httpx.AsyncClient`)
8. **Заменить `python-jose` на `PyJWT`**
9. **Исправить JWT cookie** (`secure=True`, `HttpOnly`, `SameSite`)
10. **Добавить atomic транзакцию** в `DeadlineService.sync()`
11. **Исправить десинхрон уведомлений**
12. **Добавить Error Boundary**
13. **Унифицировать `Base`** — один `declarative_base()`
14. **Исправить `testpaths`** и добавить pytest-тесты для auth, API

### Среднесрочно (2-4 недели)

15. **Rate limiting** на `/deadlines/sync` (Redis)
16. **Шифрование `cookies_json`**
17. **Docker-compose** (PostgreSQL + backend + frontend)
18. **GitHub Actions** (lint, test)
19. **Live API для конспектов**
20. **Календарь (все события)**

### Долгосрочно (1-2 месяца)

21. **Push-уведомления / Telegram**
22. **AI-ассистент**
23. **E2E тесты** (Playwright)
24. **Мобильное PWA** (pull-to-refresh, offline, safe area)

---

## Оценка времени до MVP (100%)

| Работа | Оценка |
|--------|--------|
| P0 баги (8 шт) | 2-3 дня |
| P1 баги (10 шт) | 1-2 недели |
| P2 баги (7 шт) | 2-3 недели |
| Документация + деплой | 3-5 дней |
| Доп. тесты | 1 неделя |
| **Итого до стабильного MVP** | **3-4 недели** |

---

*Аудит проведён автоматически с помощью 3 параллельных агентов-аналитиков. Все найденные проблемы требуют ручной проверки перед исправлением.*
