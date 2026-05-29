"""Главный файл FastAPI приложения StudyCore backend.

Предоставляет REST API для фронтенда. На текущий момент
реализован единственный роут — авторизация в Netology.

Запуск:
    cd backend && uvicorn main:app --reload --port 8000

Документация (Swagger UI):
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth_router import router as auth_router

# ---------------------------------------------------------------------------
# Создание FastAPI приложения
# ---------------------------------------------------------------------------
# title: имя приложения (отображается в Swagger UI)
# version: текущая версия API
# docs_url: путь к Swagger UI (None — отключить)
# redoc_url: путь к ReDoc (None — отключить)
# ---------------------------------------------------------------------------
app = FastAPI(
    title="StudyCore API",
    version="0.9.2",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------------------------------
# Фронтенд запускается на localhost:5173 (Vite dev server).
# Бэкенд — на localhost:8000. Без CORS браузер блокирует
# запросы между разными origin'ами.
#
# allow_origins: список доменов, которым разрешён доступ.
#    ["*"] — разрешить всем (только для разработки!).
# allow_credentials: разрешить передачу cookies.
# allow_methods: разрешить все HTTP-методы.
# allow_headers: разрешить все заголовки.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: заменить на конкретный origin в production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Подключение роутеров
# ---------------------------------------------------------------------------
# Все endpoint'ы авторизации доступны по префиксу /api/auth/*
# ---------------------------------------------------------------------------
app.include_router(auth_router, prefix="/api")


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    """Health-check endpoint.

    Returns:
        dict: Статус приложения.
    """
    return {"status": "ok", "service": "StudyCore API"}
