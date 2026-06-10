"""Главный файл FastAPI приложения StudyCore backend.

Предоставляет REST API для фронтенда с поддержкой:
- Авторизации Netology
- PostgreSQL сессий
- JWT-cookie аутентификации
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth_router import router as auth_router
from backend.api.calendar_router import router as calendar_router
from backend.api.deadlines_router import router as deadlines_router
from backend.api.programs_router import router as programs_router
from backend.api.summary_router import router as summary_router
from backend.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: подключение к БД при старте, отключение при остановке."""
    # Startup
    print("🚀 StudyCore API запускается...")
    yield
    # Shutdown
    print("🛑 StudyCore API останавливается...")
    await engine.dispose()


app = FastAPI(
    title="StudyCore API",
    version="0.9.3",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
# При allow_credentials=True нельзя использовать allow_origins=["*"] —
# браузер отклонит Set-Cookie. Указываем конкретные origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",   # Vite dev server
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(auth_router, prefix="/api")
app.include_router(programs_router, prefix="/api")
app.include_router(deadlines_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(summary_router, prefix="/api")


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    """Health-check endpoint."""
    return {"status": "ok", "service": "StudyCore API"}
