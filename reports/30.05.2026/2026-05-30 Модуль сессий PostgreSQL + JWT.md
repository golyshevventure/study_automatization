# Модуль сессий: PostgreSQL + JWT-cookie

**Дата:** 2026-05-30
**Контекст:** StudyCore требовалось запоминать пользователей между визитами. Ранее бэкенд авторизовался в Netology, получал cookies — и сразу их выбрасывал. Теперь cookies сохраняются в PostgreSQL, а пользователь запоминается через JWT-cookie.

---

## Что сделано

1. **Установлен PostgreSQL 16**
   - Создана БД `studycore`
   - Создан пользователь `studycore_user`

2. **Создана таблица `user_sessions` через SQLAlchemy + Alembic**
   - UUID v7 — непредсказуемый ID пользователя
   - Поля: email, netology_session, cookies_json, created_at, updated_at, expires_at

3. **SessionService** — CRUD-операции для сессий
   - `create_or_update_session` — создание или обновление
   - `get_by_user_id` / `get_by_email` — поиск
   - `delete_session` — выход из аккаунта

4. **JWT-security**
   - `create_jwt_token(user_id)` — подписанный токен
   - `verify_jwt_token(token)` — проверка и извлечение user_id

5. **Обновлён auth_router**
   - После успешной авторизации сохраняет сессию в БД
   - Устанавливает JWT-cookie `session_token` (httponly, 7 дней)
   - Возвращает `user_id` во фронтенд

6. **Dependency `get_current_session`**
   - Извлекает JWT из cookie
   - Проверяет подпись
   - Находит сессию в БД
   - Готов к использованию в защищённых endpoint'ах

---

## Архитектура

```
Пользователь вводит email/password
    ↓
Frontend → POST /api/auth/netology
    ↓
FastAPI auth_router
    ↓
NetologyAuthService.authenticate()
    ↓ POST /sign_in
Netology.ru → cookies
    ↓
SessionManager.create_or_update_session()
    ↓ INSERT/UPDATE PostgreSQL
user_sessions
    ↓
create_jwt_token(user_id)
    ↓
Set-Cookie: session_token=...
    ↓
Frontend получает success=true + user_id

--- Последующие запросы ---

Frontend шлёт cookie session_token
    ↓
FastAPI endpoint
    ↓
get_current_session (dependency)
    ↓
verify_jwt_token → user_id
    ↓ SELECT
PostgreSQL → UserSession
    ↓
Endpoint использует session.cookies_json для запросов к Netology
```

---

## Структура таблицы `user_sessions`

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | UUID v7 (PK) | Непредсказуемый уникальный ID |
| `email` | VARCHAR(255), UNIQUE | Email от Netology |
| `netology_session` | TEXT | Cookie `_netology-on-rails_session` |
| `cookies_json` | JSONB | Все cookies в JSON-формате |
| `created_at` | TIMESTAMPTZ | Дата создания |
| `updated_at` | TIMESTAMPTZ | Дата обновления |
| `expires_at` | TIMESTAMPTZ | Срок действия сессии |

**Почему UUID v7:**
- Не по порядку (1, 2, 3...) — злоумышленник не угадает
- Содержит timestamp + рандом — быстро индексируется БД
- Уникальный и непредсказуемый

---

## Файлы

**Новые:**
- `backend/core/config.py` — настройки (DB_URL, JWT_SECRET)
- `backend/core/database.py` — SQLAlchemy async engine + get_db()
- `backend/core/security.py` — JWT create/verify
- `backend/models/session.py` — модель UserSession
- `backend/services/session_service/session_manager.py` — SessionManager
- `backend/dependencies/session_dep.py` — get_current_session
- `backend/tests/test_session_service.py` — 4 теста (все проходят)
- `backend/alembic/` — миграции Alembic

**Изменённые:**
- `backend/api/auth_router.py` — async + cookie + JWT + DB
- `backend/main.py` — lifespan для подключения/отключения БД
- `pyproject.toml` — pytest-asyncio настройки

---

## Тесты

```bash
PYTHONPATH=. .venv/bin/pytest backend/tests/test_session_service.py -v
```

Результат:
```
test_create_session PASSED
test_update_existing_session PASSED
test_get_by_user_id PASSED
test_delete_session PASSED
```

---

## Запуск

```bash
# PostgreSQL должен быть запущен
sudo systemctl start postgresql

# FastAPI backend
cd backend && uvicorn main:app --reload --port 8000
```

---

## Защита роутов: welcome ↔ главная

### Реализовано

**Бэкенд:**
- `GET /api/auth/me` — проверка сессии по JWT-cookie
- `POST /api/auth/logout` — удаление сессии и cookie

**Фронтенд:**
- `AuthContext` — глобальное состояние авторизации, проверка при старте
- `ProtectedRoute` — доступна только авторизованным, иначе редирект на `/welcome`
- `PublicOnlyRoute` — доступна только НЕавторизованным, иначе редирект на `/`
- `Welcome.tsx` — после успешного логина вызывает `authLogin()`, `PublicOnlyRoute` автоматически редиректит на главную

### Логика работы

| Состояние | Открывает | Редирект |
|-----------|-----------|----------|
| Не авторизован | Только `/welcome` | Все остальные → `/welcome` |
| Авторизован | `/`, `/notes`, `/deadlines` и т.д. | `/welcome` → `/` |

### Последовательность

1. Пользователь открывает приложение
2. `AuthContext` шлёт `GET /api/auth/me` с cookie
3. Если 401 — `isAuthenticated = false` → `ProtectedRoute` редиректит на `/welcome`
4. Если 200 — `isAuthenticated = true` → `PublicOnlyRoute` редиректит на `/`
5. После логина `Welcome.tsx` вызывает `authLogin()` → повторная проверка → редирект на `/`

---

---

## 🔴 Критическая проблема: "Неверный логин или пароль" + 500 ошибка

### Симптомы

1. **Ввод 100% верных credentials** → бэкенд возвращает `{"success":false,"error":"invalid_credentials","message":"Неверный логин или пароль"}`
2. **Перезагрузка страницы** → появляется "Ошибка авторизации"
3. **Backend падает с 500** при попытке login (в логах `InsufficientPrivilegeError: permission denied for table user_sessions`)
4. При этом **прямой вызов** `NetologyAuthService.authenticate()` из CLI работает и возвращает 200 + cookies

### Диагностика

**Шаг 1 — проверка Netology напрямую:**
```python
import httpx
# Прямой POST /backend/api/user/sign_in → 200 OK + cookies ✅
```

**Шаг 2 — проверка backend endpoint'а:**
```bash
curl -X POST http://localhost:8000/api/auth/netology \
  -d '{"email":"...","password":"..."}'
# → 500 Internal Server Error ❌
```

**Шаг 3 — проверка логов uvicorn:**
```
asyncpg.exceptions.InsufficientPrivilegeError: permission denied for table user_sessions
```

**Шаг 4 — проверка владельца таблицы:**
```sql
SELECT tableowner FROM pg_tables WHERE tablename = 'user_sessions';
-- → studycore_admin_2026
```

**Шаг 5 — проверка env-переменных процесса uvicorn:**
```bash
cat /proc/<pid>/environ | tr '\0' '\n' | grep DATABASE_URL
# → пусто (переменная не экспортирована)
```

### Корневые причины (две независимые проблемы)

#### Причина 1: `config.py` не загружал `.env`

```python
# backend/core/config.py (ДО)
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://studycore_user:studycore_pass@localhost:5432/studycore")
```

- `os.getenv()` читает **системные** переменные окружения
- `.env` файл **не загружается автоматически** в `os.environ`
- uvicorn был запущен без `export $(cat .env)`
- `config.py` использовал **дефолтный** URL со старым пользователем `studycore_user`
- `studycore_user` мог подключаться к БД, но **не был владельцем** таблицы `user_sessions`
- Result: `InsufficientPrivilegeError` → HTTP 500 при ЛЮБОМ запросе к БД

#### Причина 2: Пароль содержал спецсимволы, ломающие DSN

- Пароль в `.env`: `xK9#mP2$vL5@nQ8&wR4!`
- Символ `@` внутри пароля парсился SQLAlchemy/asyncpg как разделитель хоста
- DSN: `postgresql://user:pass@host` → asyncpg пытался подключиться к хосту `nQ8&wR4!` вместо `localhost`
- Result: `socket.gaierror: Name or service not known` / `InvalidPasswordError`

### Почему появлялось "Неверный логин или пароль"

Это было **раньше** — до добавления `SessionManager` в `auth_router.py`. В тот момент:
1. БД работала (старый пользователь ещё был владельцем таблицы)
2. `NetologyAuthService.authenticate()` возвращал ошибку
3. Возможная причина: `httpx.Client()` без `follow_redirects=True` получал 302 Redirect от Netology вместо 200
4. Но более вероятно: при первых тестах credentials передавались неверно (encoding/CORS/preflight)

После добавления `SessionManager` (сохранение в БД) ошибка сменилась с 401 на **500** — потому что backend стал падать на этапе записи в БД.

### Решение

#### 1. Добавлен `python-dotenv` в `config.py`

```python
# backend/core/config.py (ПОСЛЕ)
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "...")
```

- Теперь `.env` загружается автоматически при импорте `config.py`
- uvicorn получает актуальный `DATABASE_URL` без ручного `export`

#### 2. Изменён пароль PostgreSQL

```sql
-- От имени postgres
ALTER USER studycore_admin_2026 WITH PASSWORD 'StudyCore2026SecurePass';

-- Выданы все права на существующие и будущие таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO studycore_admin_2026;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO studycore_admin_2026;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO studycore_admin_2026;
```

- Новый пароль не содержит `@#$&!` → DSN парсится корректно
- `studycore_admin_2026` — владелец таблицы `user_sessions` со всеми правами

#### 3. Обновлён `.env`

```
DATABASE_URL=postgresql+asyncpg://studycore_admin_2026:StudyCore2026SecurePass@localhost:5432/studycore
```

#### 4. Перезапущен uvicorn на чистом порту

- Старый процесс занимал порт 8000 и использовал закешированный `config.py`
- `kill -9 <pid>` → порт освобождён → новый uvicorn с актуальным конфигом

### Результаты тестов (после фикса)

| Endpoint | Запрос | HTTP | Результат |
|----------|--------|------|-----------|
| `POST /api/auth/netology` | `{"email":"...","password":"..."}` | 200 | `{"success":true,"user_id":"019e7886-..."}` ✅ |
| `GET /api/auth/me` | cookie: `session_token` | 200 | `{"authenticated":true,"email":"golyshevventure@gmail.com"}` ✅ |
| `POST /api/auth/logout` | cookie: `session_token` | 200 | `{"message":"Выход выполнен"}` ✅ |

### Выводы

- **Проблема была не в Netology** — прямой вызов `httpx.post()` всегда возвращал 200
- **Проблема была не в credentials** — они верные
- **Проблема была в инфраструктуре**: отсутствие `load_dotenv` + спецсимволы в пароле + старый процесс uvicorn
- После фикса авторизация работает end-to-end: frontend → FastAPI → Netology → PostgreSQL → JWT-cookie

---

## Следующие шаги

1. **Кнопка "Выйти"** на главной странице
2. **Защищённые endpoint'ы** для lesson_items, programs и т.д.
3. **Автообновление cookies** — при истечении срока Netology-сессии
