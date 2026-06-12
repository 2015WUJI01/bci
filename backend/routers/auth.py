import hashlib

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models import User
from backend.schemas import LoginRequest, AuthResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def get_current_user(token: str = Header(alias="x-auth-token"), session: AsyncSession = Depends(get_session)):
    if not token:
        raise HTTPException(401, "未登录")
    r = await session.execute(select(User).where(User.token == token))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "登录已过期")
    return user


async def get_optional_user(token: str | None = Header(default=None, alias="x-auth-token"), session: AsyncSession = Depends(get_session)):
    if not token:
        return None
    r = await session.execute(select(User).where(User.token == token))
    return r.scalar_one_or_none()


def hash_password(password: str, salt: str) -> str:
    """SHA-256 hashing with salt."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, session: AsyncSession = Depends(get_session)):
    email = req.email.strip().lower()
    r = await session.execute(select(User).where(User.username == email))
    user = r.scalar_one_or_none()

    if not user:
        # Auto-register with email + password
        if not req.password or len(req.password) < 3:
            raise HTTPException(400, "密码至少3位")
        salt = User.generate_salt()
        user = User(
            username=email,
            password_hash=hash_password(req.password, salt),
            salt=salt,
            token=User.generate_token(),
            nickname=req.nickname or email.split("@")[0],
        )
        session.add(user)
        await session.commit()
        return AuthResponse(token=user.token, username=user.nickname or user.username, user_id=user.id, email=user.username)

    # Existing user: verify password
    if not req.password:
        raise HTTPException(400, "请输入密码")

    if user.password_hash:
        # Normal login - verify password
        if user.password_hash != hash_password(req.password, user.salt):
            raise HTTPException(401, "密码错误")
    else:
        # First-time password set (migrate from password-less account)
        user.salt = User.generate_salt()
        user.password_hash = hash_password(req.password, user.salt)

    # Refresh token
    user.token = User.generate_token()
    if req.nickname:
        user.nickname = req.nickname
    await session.commit()

    return AuthResponse(token=user.token, username=user.nickname or user.username, user_id=user.id, email=user.username)


@router.get("/me")
async def me(user: User | None = Depends(get_optional_user)):
    if not user:
        return {"ok": False}
    return {"ok": True, "token": user.token, "username": user.nickname or user.username, "user_id": user.id, "email": user.username}
