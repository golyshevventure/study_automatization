"""FastAPI роутер для авторизации в Netology.

Предоставляет endpoint POST /api/auth/netology, который:
1. Авторизует пользователя в Netology
2. Сохраняет cookies в PostgreSQL
3. Устанавливает JWT-cookie для запоминания сессии
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import create_jwt_token
from backend.services.auth_service.netology_auth import NetologyAuthError, NetologyAuthService
from backend.services.session_service.session_manager import SessionManager

# ---------------------------------------------------------------------------
# Pydantic-схемы запросов и ответов
# ---------------------------------------------------------------------------


class AuthRequest(BaseModel):
    """Тело запроса на авторизацию."""

    email: str
    password: str


class AuthResponse(BaseModel):
    """Тело ответа на авторизацию."""

    success: bool
    message: str | None = None
    error: str | None = None
    user_id: str | None = None


# ---------------------------------------------------------------------------
# Роутер
# ---------------------------------------------------------------------------

router = APIRouter(tags=["auth"])
_auth_service = NetologyAuthService(timeout=15.0)


@router.post(
    "/auth/netology",
    response_model=AuthResponse,
    summary="Авторизация в Netology",
    description=(
        "Принимает email и password, авторизуется в Netology, "
        "сохраняет cookies в БД и устанавливает JWT-cookie."
    ),
)
async def authenticate_netology(
    request: AuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Авторизовать пользователя и создать сессию.

    Args:
        request: Объект AuthRequest с email и password.
        response: FastAPI Response для установки cookie.
        db: Асинхронная сессия БД.

    Returns:
        AuthResponse с результатом авторизации и user_id.
    """
    try:
        # 1. Авторизация в Netology
        cookies = _auth_service.authenticate(request.email, request.password)

        # 2. Сохраняем сессию в БД
        manager = SessionManager(db)
        session = await manager.create_or_update_session(
            email=request.email,
            cookies=dict(cookies),
        )

        # 3. Создаём JWT-токен
        token = create_jwt_token(session.user_id)

        # 4. Устанавливаем cookie
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,  # True для HTTPS в production
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 7 дней
        )

        return AuthResponse(
            success=True,
            message="Авторизация успешна",
            user_id=str(session.user_id),
        )

    except NetologyAuthError as exc:
        error_message = str(exc)

        if "401" in error_message:
            return AuthResponse(
                success=False,
                error="invalid_credentials",
                message="Неверный логин или пароль",
            )

        if "Сетевая ошибка" in error_message:
            return AuthResponse(
                success=False,
                error="network_error",
                message="Ошибка авторизации. Попробуйте ещё раз",
            )

        return AuthResponse(
            success=False,
            error="unexpected_error",
            message="Ошибка авторизации. Попробуйте ещё раз",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {exc}",
        ) from exc
