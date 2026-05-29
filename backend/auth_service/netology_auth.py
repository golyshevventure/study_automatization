"""Модуль авторизации в Netology через HTTP API.

Использует endpoint POST /backend/api/user/sign_in.
Не сохраняет и не логирует credentials.
"""

import httpx
from typing import Optional

NETOLOGY_SIGN_IN_URL = "https://netology.ru/backend/api/user/sign_in"


class NetologyAuthError(Exception):
    """Ошибка авторизации в Netology."""
    pass


class NetologyAuthService:
    """Сервис авторизации в Netology.

    Получает логин/пароль, отправляет POST /sign_in,
    возвращает cookies (session_id и пр.).

    НЕ сохраняет и НЕ логирует credentials.
    НЕ выводит cookies в stdout/stderr.
    """

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def authenticate(self, email: str, password: str) -> httpx.Cookies:
        """Авторизоваться в Netology и вернуть cookies.

        Args:
            email: Email от аккаунта Netology.
            password: Пароль от аккаунта Netology.

        Returns:
            httpx.Cookies с _netology-on-rails_session и прочими cookies.

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

        return client.cookies
