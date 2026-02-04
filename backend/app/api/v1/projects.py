"""Project management endpoints."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, desc

from app.api.deps import DbSession, CurrentUser, UserProject, Pagination
from app.core.storage import storage
from app.models import Project, ProjectStatus
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectListResponse, PaginatedResponse, MessageResponse,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_projects(
    user: CurrentUser, db: DbSession, pagination: Pagination,
    status_filter: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
):
    """List all projects for the current user."""
    query = select(Project).where(Project.user_id == user.id)
    count_query = select(func.count(Project.id)).where(Project.user_id == user.id)
    
    if status_filter is not None:
        query = query.where(Project.status == status_filter)
        count_query = count_query.where(Project.status == status_filter)
    
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))
        count_query = count_query.where(Project.name.ilike(f"%{search}%"))
    
    total = (await db.execute(count_query)).scalar()
    
    sort_column = getattr(Project, sort_by, Project.created_at)
    query = query.order_by(desc(sort_column) if sort_desc else sort_column)
    query = query.offset(pagination.offset).limit(pagination.size)
    
    projects = (await db.execute(query)).scalars().all()
    pages = (total + pagination.size - 1) // pagination.size if total > 0 else 1
    
    return PaginatedResponse(
        items=[ProjectListResponse.model_validate(p) for p in projects],
        total=total, page=pagination.page, size=pagination.size, pages=pages,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, user: CurrentUser, db: DbSession):
    """Create a new project."""
    existing = await db.execute(
        select(Project).where(Project.user_id == user.id, Project.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project with this name already exists")
    
    project = Project(
        user_id=user.id, name=data.name, description=data.description,
        latitude=data.latitude, longitude=data.longitude,
        location_name=data.location_name, status=ProjectStatus.CREATED,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project: UserProject):
    """Get project details."""
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(data: ProjectUpdate, project: UserProject, db: DbSession):
    """Update project details."""
    if project.is_processing:
        raise HTTPException(status_code=400, detail="Cannot update while processing")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(project: UserProject, db: DbSession):
    """Delete a project and all associated data."""
    if project.is_processing:
        raise HTTPException(status_code=400, detail="Cannot delete while processing")
    
    try:
        await storage.delete_folder(project.storage_prefix)
    except Exception:
        pass
    
    await db.delete(project)
    await db.commit()
    return MessageResponse(message=f"Project '{project.name}' deleted")
