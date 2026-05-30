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

## Следующие шаги

1. **Кнопка "Выйти"** на главной странице
2. **Защищённые endpoint'ы** для lesson_items, programs и т.д.
3. **Автообновление cookies** — при истечении срока Netology-сессии
