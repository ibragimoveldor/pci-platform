"""
Authentication endpoints.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, CurrentUser
from app.core.security import (
    hash_password,
    verify_password,
    verify_token,
    TokenPair,
)
from app.models import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    TokenRefresh,
    MessageResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    db: DbSession,
):
    """Register a new user account."""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: DbSession):
    """Authenticate user and return tokens."""
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    tokens = TokenPair(user.id)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh, db: DbSession):
    """Refresh access token using refresh token."""
    user_id = verify_token(data.refresh_token, token_type="refresh")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    tokens = TokenPair(user.id)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: CurrentUser):
    """Get current authenticated user info."""
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update current user profile."""
    if data.full_name is not None:
        user.full_name = data.full_name
    
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/logout", response_model=MessageResponse)
async def logout(user: CurrentUser):
    """Logout current user."""
    return MessageResponse(message="Successfully logged out")
