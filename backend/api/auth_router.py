"""FastAPI роутер для авторизации в Netology.

Предоставляет endpoint POST /api/auth/netology, который принимает
email и password пользователя, отправляет их в API Netology
и возвращает статус авторизации.

Модуль НЕ сохраняет credentials и cookies.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.services.auth_service.netology_auth import NetologyAuthService, NetologyAuthError

# ---------------------------------------------------------------------------
# Pydantic-схемы запросов и ответов
# ---------------------------------------------------------------------------

class AuthRequest(BaseModel):
    """Тело запроса на авторизацию.

    Attributes:
        email: Email от аккаунта Netology.
        password: Пароль от аккаунта Netology.
    """
    email: str
    password: str


class AuthResponse(BaseModel):
    """Тело ответа на авторизацию.

    Attributes:
        success: True если авторизация прошла успешно.
        message: Человекочитаемое сообщение (опционально).
        error: Код ошибки (опционально, только при success=False).
    """
    success: bool
    message: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Роутер
# ---------------------------------------------------------------------------

router = APIRouter(tags=["auth"])

# Единственный экземпляр сервиса авторизации на уровне модуля.
# NetologyAuthService stateless — можно использовать один инстанс
# для всех запросов.
_auth_service = NetologyAuthService(timeout=15.0)


@router.post(
    "/auth/netology",
    response_model=AuthResponse,
    summary="Авторизация в Netology",
    description=(
        "Принимает email и password, отправляет их в API Netology "
        "(POST /backend/api/user/sign_in). При успехе возвращает "
        "{success: true}. При ошибке — код ошибки и сообщение. "
        "Cookies и credentials НЕ сохраняются и НЕ возвращаются."
    ),
)
def authenticate_netology(request: AuthRequest) -> AuthResponse:
    """Авторизовать пользователя в Netology.

    Args:
        request: Объект AuthRequest с email и password.

    Returns:
        AuthResponse с результатом авторизации.

    Raises:
        HTTPException: только при неожиданных ошибках (500).
            Все ожидаемые ошибки (401, timeout) возвращаются
            через AuthResponse с success=False.
    """
    try:
        # -------------------------------------------------------------------
        # 1. Отправляем запрос в Netology API
        # -------------------------------------------------------------------
        # NetologyAuthService.authenticate() отправляет POST /sign_in
        # и возвращает httpx.Cookies при статусе 200.
        # При 401 или сетевой ошибке выбрасывает NetologyAuthError.
        #
        # Полученные cookies намеренно игнорируются — модуль
        # выполняет только проверку валидности credentials.
        # -------------------------------------------------------------------
        _auth_service.authenticate(request.email, request.password)

        # -------------------------------------------------------------------
        # 2. Успешная авторизация
        # -------------------------------------------------------------------
        return AuthResponse(
            success=True,
            message="Авторизация успешна",
        )

    except NetologyAuthError as exc:
        # -------------------------------------------------------------------
        # 3. Ожидаемые ошибки от NetologyAuthService
        # -------------------------------------------------------------------
        # Сервис выбрасывает NetologyAuthError с разными сообщениями:
        #   - "Неверный логин или пароль (HTTP 401)" → invalid_credentials
        #   - "Сетевая ошибка: ..." → network_error
        #   - "Неожиданный статус ..." → unexpected_error
        #
        # Все они мапятся на AuthResponse с success=False и кодом ошибки.
        # -------------------------------------------------------------------
        error_message = str(exc)

        if "401" in error_message:
            # Netology вернула 401 Unauthorized — неверные credentials
            return AuthResponse(
                success=False,
                error="invalid_credentials",
                message="Неверный логин или пароль",
            )

        if "Сетевая ошибка" in error_message:
            # Таймаут или другая сетевая проблема
            return AuthResponse(
                success=False,
                error="network_error",
                message="Ошибка авторизации. Попробуйте ещё раз",
            )

        # Любая другая ошибка от NetologyAuthService
        return AuthResponse(
            success=False,
            error="unexpected_error",
            message="Ошибка авторизации. Попробуйте ещё раз",
        )

    except Exception as exc:
        # -------------------------------------------------------------------
        # 4. Неожиданные ошибки (баги, некорректный ответ сервера и т.д.)
        # -------------------------------------------------------------------
        # Такие ошибки логируем через HTTPException 500 — они
        # требуют внимания разработчика, а не просто повторной попытки.
        # -------------------------------------------------------------------
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {exc}",
        ) from exc
