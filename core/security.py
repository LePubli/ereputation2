"""
Sécurité : hash de mot de passe (bcrypt) + JWT.

Bien que Phase 1 n'active pas encore l'auth complète sur toutes les routes,
on prépare déjà l'infrastructure pour la Phase 2.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash bcrypt d'un mot de passe."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """Crée un JWT signé HS256."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    """Crée un JWT de refresh longue durée."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Décode un JWT. Retourne None si invalide."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

def verify_token(token: str) -> dict:
    """Décode et vérifie un JWT — usage WebSocket."""
    from jose import jwt, JWTError
    from core.config import settings

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Token invalide: {e}") 
