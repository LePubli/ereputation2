"""Routes d'authentification JWT."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser, hash_token, revoke_refresh_token, validate_refresh_token
from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from models.database.refresh_token import RefreshToken
from models.database.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# --- Schémas ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class RefreshRequest(BaseModel):
    refresh_token: str

class UserMe(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# --- Endpoints ---

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authentification → retourne access_token + refresh_token."""
    stmt = select(User).where(User.email == body.email, User.is_active.is_(True))
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    access_token = create_access_token(str(user.id), extra={"role": user.role, "email": user.email})
    refresh_token_str = create_refresh_token(str(user.id))

    # Stocker le refresh token hashé
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(rt)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Renouvelle l'access_token depuis un refresh_token valide (rotation)."""
    user = await validate_refresh_token(body.refresh_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré",
        )

    # Rotation : révoque l'ancien, émet un nouveau
    await revoke_refresh_token(body.refresh_token, db)

    access_token = create_access_token(str(user.id), extra={"role": user.role, "email": user.email})
    new_refresh = create_refresh_token(str(user.id))

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(rt)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Révoque le refresh token (déconnexion)."""
    await revoke_refresh_token(body.refresh_token, db)
    return None


@router.get("/me", response_model=UserMe)
async def me(current_user: CurrentUser):
    """Retourne l'utilisateur connecté."""
    return UserMe(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Change le mot de passe de l'utilisateur connecté."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (min 8 caractères)")

    current_user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return None
