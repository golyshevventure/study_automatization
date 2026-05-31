"""Модуль авторизации в Netology через HTTP API.

Использует endpoint POST /backend/api/user/sign_in.
Не сохраняет и не логирует credentials.
"""

import httpx
from typing import NamedTuple, Optional

NETOLOGY_SIGN_IN_URL = "https://netology.ru/backend/api/user/sign_in"


class NetologyAuthError(Exception):
    """Ошибка авторизации в Netology."""
    pass


class AuthResult(NamedTuple):
    """Результат успешной авторизации в Netology.

    Attributes:
        cookies: Cookies сессии (session_id и пр.).
        full_name: Полное имя пользователя (или None).
        avatar_url: URL аватара пользователя (или None).
    """
    cookies: httpx.Cookies
    full_name: Optional[str]
    avatar_url: Optional[str]


class NetologyAuthService:
    """Сервис авторизации в Netology.

    Получает логин/пароль, отправляет POST /sign_in,
    возвращает cookies и профиль пользователя.

    НЕ сохраняет и НЕ логирует credentials.
    НЕ выводит cookies в stdout/stderr.
    """

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def authenticate(self, email: str, password: str) -> AuthResult:
        """Авторизоваться в Netology и вернуть cookies + профиль.

        Args:
            email: Email от аккаунта Netology.
            password: Пароль от аккаунта Netology.

        Returns:
            AuthResult с cookies, full_name и avatar_url.

        Raises:
            NetologyAuthError: при ошибке сети, неверных credentials или
                неожиданном ответе сервера.
        """
        data = {
            "login": email,
            "password": password,
            "remember": "1",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(NETOLOGY_SIGN_IN_URL, data=data)
        except httpx.TransportError as exc:
            raise NetologyAuthError(f"Сетевая ошибка: {exc}") from exc

        if response.status_code == 401:
            raise NetologyAuthError(
                "Неверный логин или пароль (HTTP 401)"
            )

        if response.status_code != 200:
            raise NetologyAuthError(
                f"Неожиданный статус {response.status_code}: "
                f"{response.text[:200]}"
            )

        # Парсим профиль пользователя из ответа
        full_name: Optional[str] = None
        avatar_url: Optional[str] = None
        try:
            payload = response.json()
            user = payload.get("app_options", {}).get("user", {})
            full_name = user.get("full_name")
            avatar_url = user.get("medium_avatar_url")
        except Exception:
            # Если JSON сломан — не критично, просто нет профиля
            pass

        return AuthResult(
            cookies=client.cookies,
            full_name=full_name,
            avatar_url=avatar_url,
        )
