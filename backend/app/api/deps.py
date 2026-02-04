"""
API Dependencies for dependency injection.
"""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.models import User, Project
from app.schemas import PaginationParams


# =============================================================================
# Security
# =============================================================================
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get current authenticated user.
    
    Raises HTTPException 401 if not authenticated.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = verify_token(credentials.credentials, token_type="access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency for active users only."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


async def get_current_superuser(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency for superusers only."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return user


# Optional user (for public endpoints that behave differently when logged in)
async def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# =============================================================================
# Resource Access
# =============================================================================
async def get_user_project(
    project_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    """
    Get a project owned by the current user.
    
    Raises HTTPException 404 if not found or not owned by user.
    """
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )
    project = result.scalar_one_or_none()
    
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    return project


# =============================================================================
# Pagination
# =============================================================================
def get_pagination(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginationParams:
    """Get pagination parameters."""
    return PaginationParams(page=page, size=size)


# =============================================================================
# Type Aliases for cleaner signatures
# =============================================================================
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserProject = Annotated[Project, Depends(get_user_project)]
Pagination = Annotated[PaginationParams, Depends(get_pagination)]
