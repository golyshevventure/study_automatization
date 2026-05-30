"""JWT-токены для сессий.

Создание и проверка JWT, которые хранятся в cookie браузера.
"""

import uuid_utils as uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from backend.core.config import settings


def create_jwt_token(user_id: uuid.UUID) -> str:
    """Создать JWT-токен для пользователя.

    Args:
        user_id: UUID v7 пользователя.

    Returns:
        str: подписанный JWT-токен.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # subject = user_id
        "iat": now,           # issued at
        "exp": now + timedelta(days=settings.JWT_EXPIRE_DAYS),
        "type": "session",
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_jwt_token(token: str) -> Optional[uuid.UUID]:
    """Проверить JWT-токен и вернуть user_id.

    Args:
        token: JWT-строка из cookie.

    Returns:
        UUID или None, если токен невалидный/истёкший.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        return uuid.UUID(user_id_str)
    except JWTError:
        return None
