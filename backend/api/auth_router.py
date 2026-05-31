"""FastAPI роутер для авторизации в Netology.

Предоставляет endpoints:
- POST /api/auth/netology — авторизация + установка JWT-cookie
- GET /api/auth/me — проверка текущей сессии + профиль
- POST /api/auth/logout — выход из аккаунта
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import create_jwt_token, verify_jwt_token
from backend.dependencies.session_dep import get_current_session
from backend.models.session import UserSession
from backend.services.auth_service.netology_auth import NetologyAuthError, NetologyAuthService
from backend.services.session_service.session_manager import SessionManager

# ---------------------------------------------------------------------------
# Pydantic-схемы
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


class MeResponse(BaseModel):
    """Ответ на проверку текущей сессии с профилем пользователя."""

    authenticated: bool
    user_id: str | None = None
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None


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
        "сохраняет cookies и профиль в БД и устанавливает JWT-cookie."
    ),
)
async def authenticate_netology(
    request: AuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Авторизовать пользователя и создать сессию."""
    try:
        # 1. Авторизация в Netology (cookies + профиль)
        auth_result = _auth_service.authenticate(request.email, request.password)

        # 2. Сохраняем сессию и профиль в БД
        manager = SessionManager(db)
        session = await manager.create_or_update_session(
            email=request.email,
            cookies=dict(auth_result.cookies),
            full_name=auth_result.full_name,
            avatar_url=auth_result.avatar_url,
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


@router.get(
    "/auth/me",
    response_model=MeResponse,
    summary="Проверка текущей сессии",
    description="Возвращает данные текущего пользователя (профиль + JWT-cookie).",
)
async def get_me(
    session: UserSession = Depends(get_current_session),
) -> MeResponse:
    """Проверить текущую сессию.

    Извлекает session_token из cookie, проверяет JWT
    и возвращает данные пользователя из БД (включая кешированный профиль).
    """
    return MeResponse(
        authenticated=True,
        user_id=str(session.user_id),
        email=session.email,
        full_name=session.full_name,
        avatar_url=session.avatar_url,
    )


@router.post(
    "/auth/logout",
    summary="Выход из аккаунта",
    description="Удаляет JWT-cookie и сессию из БД.",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Выйти из аккаунта.

    Удаляет сессию из БД и очищает cookie.
    """
    token = request.cookies.get("session_token")
    if token:
        user_id = verify_jwt_token(token)
        if user_id:
            manager = SessionManager(db)
            await manager.delete_session(user_id)

    response.delete_cookie("session_token")
    return {"message": "Выход выполнен"}
