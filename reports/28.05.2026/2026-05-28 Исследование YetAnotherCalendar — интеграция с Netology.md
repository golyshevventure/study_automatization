# Исследование: YetAnotherCalendar — что полезно для StudyCore

**Дата:** 2026-05-28
**Источник:** https://github.com/depocoder/YetAnotherCalendar
**Контекст:** Проект на FastAPI + React, интегрируется с Netology, Modeus, LMS. Цель — найти подходы, которые можно адаптировать для StudyCore.

---

## 1. Критичная находка: авторизация в Netology БЕЗ браузера

### Что нашли

```python
# backend/yet_another_calendar/web/api/netology/integration.py

async def auth_netology(username: str, password: str, timeout: int = 15) -> schema.NetologyCookies:
    async with AsyncClient(
        http2=True,
        base_url=settings.netology_base_url,
        timeout=timeout,
    ) as session:
        response = await session.post(settings.netology_sign_in_part, data={
            "login": username,
            "password": password,
            "remember": "1",
        })
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(detail='Netology error. Username/password is incorrect.',
                                status_code=response.status_code)
        response.raise_for_status()
        return schema.NetologyCookies(**session.cookies)
```

**Endpoint:** `POST https://netology.ru/backend/api/user/sign_in`

**Параметры формы:**
- `login` — email
- `password` — пароль
- `remember` — `"1"` (чтобы сессия жила дольше)

**Что возвращает:** cookie `_netology-on-rails_session` — это и есть сессия.

### Почему это революционно для StudyCore

Сейчас в StudyCore Playwright используется для **двух вещей**:
1. Авторизация (ввод логина/пароля в браузере, получение cookies)
2. Fallback скрейпинг (когда API не работает)

С прямым POST-логином Playwright нужен **только для fallback** (п.2). Авторизация станет:
- **В 10 раз быстрее** — 1-2 секунды вместо 10-15 секунд запуска браузера
- **В 100 раз стабильнее** — нет race conditions, headless-детекции, проблем с WSL
- **Без GUI** — можно запускать на сервере без дисплея

### Pydantic-модель для cookies

```python
class NetologyCookies(BaseModel):
    rails_session: str = Field(alias="_netology-on-rails_session")

async def get_cookies_from_headers(
    rails_session: Annotated[str, Header(alias="_netology-on-rails_session")],
) -> NetologyCookies:
    return NetologyCookies.model_validate({
        "_netology-on-rails_session": rails_session,
    })
```

Cookies передаются через **Header** `_netology-on-rails_session`, не через body. Это позволяет:
- Фронтенд хранить cookie и отправлять его с каждым запросом
- Бэкенд использовать dependency injection для валидации
- Легко переключаться между session-based и API-token auth

---

## 2. Endpoint'ы Netology — отличия от StudyCore

### Сравнительная таблица

| Endpoint | YetAnotherCalendar | StudyCore |
|----------|-------------------|-----------|
| **Логин** | `POST /backend/api/user/sign_in` | Playwright + browser |
| **Курсы** | `GET /backend/api/user/programs/calendar/filters` | `GET /backend/api/user/programs/progress` |
| **Программы** | `GET /backend/api/user/professions/{calendar_id}/schedule` | `GET /backend/api/user/professions/{id}/schedule` |
| **События** | `GET /backend/api/user/programs/{program_id}/schedule` | `GET /backend/api/user/student_learning/calendar` |

### Ключевое отличие: `/programs/{program_id}/schedule` vs `/student_learning/calendar`

**YetAnotherCalendar** запрашивает расписание **по каждой программе отдельно** через `asyncio.TaskGroup` (параллельно). Это даёт:
- **Меньше данных за раз** — не 370KB JSON, а десятки маленьких ответов
- **Прогрессивная загрузка** — можно показывать результаты по мере получения
- **Лучшее кэширование** — каждая программа кэшируется отдельно

**StudyCore** запрашивает **всё сразу** через `/student_learning/calendar` (370KB). Это даёт:
- **Один запрос** — меньше оверхеда
- **Полная картина** — сразу все дедлайны

**Рекомендация:** StudyCore может использовать **оба подхода**:
- `/student_learning/calendar` для быстрого получения всех дедлайнов (как сейчас)
- `/programs/{id}/schedule` для детальной загрузки конкретной программы

### Модель `LessonTask` — парсинг дедлайнов

```python
class LessonTask(BaseLesson):
    path: str
    deadline: datetime.datetime | None = Field(default=None)
    passed: bool = Field()

    @model_validator(mode='before')
    @classmethod
    def deadline_validation(cls, data: Any) -> Any:
        title = str(data.get('title', ''))
        match = _DATE_PATTERN.search(title)  # regex: DD.MM.YY
        if not match:
            return data
        day, month, year = match.groups()
        day = "01" if day == "00" else day
        month = "01" if month == "00" else month
        normalized_date = f"{day}.{month}.{year}"
        data['deadline'] = datetime.datetime.strptime(normalized_date, "%d.%m.%y").astimezone(datetime.UTC)
        return data
```

Этот подход к парсингу дедлайнов из title **гораздо надёжнее**, чем текущий в StudyCore (ожидание поля `deadline` в API). Можно объединить: если API не возвращает `deadline`, парсим из title.

---

## 3. Архитектурные решения FastAPI

### 3.1 Lifespan + правильная инициализация

```python
@asynccontextmanager
async def lifespan_setup(app: FastAPI) -> AsyncGenerator[None, None]:
    init_redis(app)
    redis = await Redis(host=settings.redis_host, port=settings.redis_port, encoding='utf-8')
    FastAPICache.init(RedisBackend(redis), prefix=settings.redis_prefix)
    try:
        yield
    finally:
        await redis.close()
```

**Полезно для StudyCore:** если добавим FastAPI backend, нужен правильный lifespan для:
- Redis подключения
- Инициализации кэша
- Graceful shutdown

### 3.2 Exception handlers

```python
app.add_exception_handler(ExceptionGroup, task_group_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(HTTPError, request_error_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
```

Особенно ценен `task_group_exception_handler` — когда `asyncio.TaskGroup` падает с несколькими исключениями, он их распаковывает и возвращает первую HTTPException.

### 3.3 Rate limiting на Redis

```python
class LoginRateLimiter:
    async def check_rate_limit(self, request: Request, redis_pool: ConnectionPool, login_type: str = "general"):
        client_ip = self._get_client_ip(request)
        cache_key = f"{login_type}_login_attempts:{client_ip}"
        # ... проверка count + lockout_time
```

**Полезно:** если StudyCore получит публичный API endpoint для логина, нужна защита от brute force. Redis-based rate limiter — готовое решение.

### 3.4 Dependency injection для cookies

```python
@router.get('/calendar/')
async def get_calendar(
    cookies: NetologyCookies = Depends(get_cookies_from_headers),
) -> SerializedEvents:
    ...
```

Клиент передаёт cookie через Header `_netology-on-rails_session`, FastAPI автоматически валидирует через Pydantic модель.

---

## 4. HTTP-клиент: HTTP/2 + retry + timeout

```python
async with AsyncClient(
    http2=True,
    base_url=settings.netology_base_url,
    timeout=timeout,
) as session:
    ...
```

### Что можно взять в StudyCore

| Фича | Реализация | Польза |
|------|-----------|--------|
| **HTTP/2** | `http2=True` | Мультиплексирование запросов, быстрее при большом количестве параллельных вызовов |
| **Retry** | `@reretry.retry(exceptions=httpx.TransportError, tries=5, delay=3)` | Автоматический retry при сетевых ошибках |
| **Base URL** | `base_url=` | Не дублировать `https://netology.ru` в каждом запросе |
| **Timeout** | `timeout=15` | Защита от зависших запросов |

---

## 5. Параллельные запросы через TaskGroup

```python
async def get_calendar(cookies, calendar_id, body):
    program_ids = await get_program_ids(cookies, calendar_id)
    serialized_events = defaultdict(list)
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for program_id in program_ids:
            tasks.append(tg.create_task(get_events_by_id(cookies, program_id=program_id)))
    for task in tasks:
        homework_events, webinars_events = task.result().get_serialized_lessons(body)
        serialized_events['homework'].extend(homework_events)
        serialized_events['webinars'].extend(webinars_events)
    return SerializedEvents.model_validate(serialized_events)
```

**Полезно для StudyCore:** сейчас `run_agent.py` обрабатывает программы **последовательно**. TaskGroup позволит загружать N программ параллельно — ускорение пропорционально N (с учётом rate limit).

---

## 6. Логирование и мониторинг

### Loguru + InterceptHandler

```python
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logger.opt(depth=2, exception=record.exc_info).log(
            level, record.getMessage(),
        )

def configure_logging() -> None:
    logging.basicConfig(handlers=[intercept_handler], level=logging.NOTSET)
    logging.getLogger("uvicorn").handlers = [intercept_handler]
    logging.getLogger("fastapi_cache").setLevel(logging.ERROR)
```

**Полезно:** StudyCore использует стандартный `logging`. Loguru даёт:
- Структурированный вывод
- Автоматическое перехватывание `uvicorn`/`httpx` логов
- Rollbar интеграцию для production

### Rollbar scrubbing

```python
rollbar.init(
    settings.rollbar_token,
    scrub_fields=[
        'password', 'token', 'auth', 'rails_session',
        '_netology-on-rails_session', 'username', 'jwt',
    ],
    locals={'enabled': False},
)
```

**Важно:** Если StudyCore станет публичным сервисом — sensitive данные (cookies, пароли) должны автоматически скрабиться из логов.

---

## 7. Тестирование: fakeredis + httpx mock

```python
# conftest.py
from fakeredis.aioredis import FakeConnection

@pytest.fixture
async def fake_redis_pool() -> AsyncGenerator[ConnectionPool, None]:
    server = FakeServer()
    server.connected = True
    pool = ConnectionPool(connection_class=FakeConnection, server=server)
    yield pool
    await pool.disconnect()

# test_netology.py
mock_cookies = schema.NetologyCookies.model_validate({"_netology-on-rails_session": "aboba"})

@pytest.mark.asyncio
async def test_auth_netology_ok(netology_client) -> None:
    netology_cookies = await integration.auth_netology("alex", "password12345")
    assert netology_cookies == schema.NetologyCookies.model_validate(netology_client.cookies)
```

**Полезно для StudyCore:**
- `fakeredis` — тесты с Redis без запущенного Redis-сервера
- `httpx` transport mocks — тесты API-клиента без реальных запросов к Netology
- `dependency_overrides` — замена зависимостей FastAPI в тестах

---

## 8. Конфигурация: Pydantic Settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    netology_base_url: str = "https://netology.ru"
    netology_sign_in_part: str = '/backend/api/user/sign_in'
    netology_get_programs_part: str = '/backend/api/user/professions/{calendar_id}/schedule'
    netology_get_events_part: str = '/backend/api/user/programs/{program_id}/schedule'
    retry_tries: int = 5
    retry_delay: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="YET_ANOTHER_CALENDAR_",
        env_file_encoding="utf-8",
    )
```

**Полезно для StudyCore:** сейчас конфигурация размазана по `os.environ` и `dotenv`. `pydantic-settings` даёт:
- Валидацию типов (URL'ы, int, Path)
- env prefix (не конфликтует с другими переменными)
- Автоматическое чтение `.env`
- `Field(default=...)` — fallback значения

---

## 9. Что точно стоит адаптировать в StudyCore

### 🔥 Приоритет: Высокий

| № | Фича | Где взять | Эффект |
|---|------|----------|--------|
| 1 | **POST-логин в Netology** | `integration.py::auth_netology()` | Убрать Playwright из авторизации, +10x скорость |
| 2 | **HTTP/2 в httpx** | `AsyncClient(http2=True)` | Быстрее при параллельных запросах |
| 3 | **Retry декоратор** | `@reretry.retry()` | Надёжность сетевых запросов |
| 4 | **TaskGroup** | `get_calendar()` | Параллельная загрузка программ |
| 5 | **Pydantic Settings** | `settings.py` | Централизованная валидация конфига |

### ⚡ Приоритет: Средний

| № | Фича | Где взять | Эффект |
|---|------|----------|--------|
| 6 | **Rate limiting** | `auth/rate_limiter.py` | Защита публичного API |
| 7 | **Loguru + scrubbing** | `log.py`, `lifespan.py` | Production-ready логи |
| 8 | **ExceptionGroup handler** | `application.py` | Стабильность async кода |
| 9 | **fakeredis для тестов** | `tests/conftest.py` | Тесты без инфраструктуры |
| 10 | **UJSONResponse** | `application.py` | Быстрее JSON для больших ответов |

### 📋 Приоритет: Низкий (для будущего)

| № | Фича | Где взять | Когда нужно |
|---|------|----------|------------|
| 11 | **Redis кэширование** | `lifespan.py` + `fastapi-cache` | Когда будет публичный API |
| 12 | **Rollbar monitoring** | `lifespan.py::init_rollbar()` | Production |
| 13 | **Docker Compose** | `docker-compose.yaml` | Деплой |
| 14 | **CORS middleware** | `application.py` | Когда фронтенд будет ходить на backend |
| 15 | **JWT для tutors** | `auth/views.py` | Роли пользователей |

---

## 10. Риски и оговорки

### Риск 1: POST-логин может сломаться

Netology может в любой момент:
- Добавить CSRF-токен на форму логина
- Добавить reCAPTCHA
- Изменить endpoint

**Митигация:** оставить Playwright как fallback. Если POST-логин возвращает 401/403/429 — автоматически переключаться на браузерную авторизацию.

### Риск 2: Endpoint'ы могут отличаться

YetAnotherCalendar работает с курсом "Разработка IT-продуктов" (программное обучение). StudyCore работает с бакалавриатом. Endpoint `/programs/{id}/schedule` может возвращать **разную структуру** для разных типов программ.

**Митигация:** протестировать на бакалавриате перед миграцией.

### Риск 3: Cookie lifetime

`_netology-on-rails_session` — это Rails-сессия. Время жизни зависит от настроек сервера. `remember=1` продлевает жизнь, но не гарантирует вечную валидность.

**Митигация:** реализовать автоматический re-login при 401 от API.

---

## Итог

**Главная ценность:** YetAnotherCalendar **подтвердил**, что авторизация в Netology возможна через простой POST-запрос. Это открывает путь к полному отказу от Playwright в StudyCore (оставив его только как fallback для edge cases).

**Вторичная ценность:** готовые архитектурные паттерны для FastAPI backend (rate limiting, lifespan, exception handling, кэширование), которые StudyCore может использовать при создании публичного API для фронтенда.
