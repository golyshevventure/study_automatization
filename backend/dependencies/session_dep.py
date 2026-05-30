"""FastAPI dependency для получения текущей сессии.

Используется в защищённых endpoint'ах.
"""

import uuid_utils as uuid
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import verify_jwt_token
from backend.models.session import UserSession
from backend.services.session_service.session_manager import SessionManager


async def get_current_session(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: AsyncSession = Depends(get_db),
) -> UserSession:
    """Извлечь текущую сессию из JWT-cookie.

    Args:
        request: FastAPI Request объект.
        session_token: JWT из cookie (автоматически извлекается).
        db: сессия БД.

    Returns:
        UserSession: активная сессия пользователя.

    Raises:
        HTTPException 401: если токен отсутствует, невалидный или сессия не найдена.
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован. Войдите в систему.",
        )

    user_id = verify_jwt_token(session_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла. Войдите заново.",
        )

    manager = SessionManager(db)
    session = await manager.get_by_user_id(user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия не найдена. Войдите заново.",
        )

    return session
