# deps.py — shared dependencies used across ALL modules
# One place for all common dependencies

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Shared dependency for ALL protected routes across all modules.
    Any route that needs authentication uses this.
    """
    from app.modules.auth.repositories.user import UserRepository

    payload = decode_token(credentials.credentials)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(payload["sub"]))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user