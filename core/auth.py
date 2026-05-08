"""
Middleware d'authentification JWT pour FastAPI.

Usage dans les routes :
    @router.get("/protected")
    async def endpoint(current_user: User = Depends(get_current_user)):
        ...

Routes publiques (pas de dépendance) :
    POST /api/v1/auth/login
    POST /api/v1/auth/refresh
    GET  /health
    GET  /
"""
import hashlib
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import decode_token
from models.database.refresh_token import RefreshToken
from models.database.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extrait et valide le JWT Bearer. Lève 401 si absent/invalide."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou désactivé",
        )
    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Version optionnelle — ne lève pas d'erreur si absent."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def hash_token(token: str) -> str:
    """Hash SHA-256 d'un refresh token pour stockage sécurisé."""
    return hashlib.sha256(token.encode()).hexdigest()


async def revoke_refresh_token(token: str, db: AsyncSession) -> None:
    """Révoque un refresh token en BDD."""
    token_hash = hash_token(token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    rt = (await db.execute(stmt)).scalar_one_or_none()
    if rt:
        rt.revoked = True
        await db.commit()


async def validate_refresh_token(token: str, db: AsyncSession) -> User | None:
    """Valide un refresh token et retourne l'user associé."""
    token_hash = hash_token(token)
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked.is_(False),
        RefreshToken.expires_at > datetime.now(timezone.utc),
    )
    rt = (await db.execute(stmt)).scalar_one_or_none()
    if not rt:
        return None

    stmt_user = select(User).where(User.id == rt.user_id, User.is_active.is_(True))
    return (await db.execute(stmt_user)).scalar_one_or_none()


# Alias pour injecter dans les routes
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
