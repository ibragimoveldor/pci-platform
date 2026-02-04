"""Image upload and management endpoints."""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy import select

from app.api.deps import DbSession, CurrentUser, UserProject
from app.config import settings
from app.core.storage import storage
from app.models import Image, Project, ProjectStatus
from app.schemas import ImageResponse, ImageUploadResponse, MessageResponse

router = APIRouter()


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_image_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {settings.allowed_image_extensions}",
        )


@router.get("", response_model=list[ImageResponse])
async def list_images(project: UserProject, db: DbSession):
    """List all images in a project."""
    result = await db.execute(
        select(Image)
        .where(Image.project_id == project.id)
        .order_by(Image.created_at)
    )
    return result.scalars().all()


@router.post("", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_images(
    project: UserProject,
    db: DbSession,
    files: list[UploadFile] = File(..., description="Image files to upload"),
):
    """Upload images to a project."""
    if project.is_processing:
        raise HTTPException(status_code=400, detail="Cannot upload while processing")
    
    uploaded_images = []
    errors = []
    
    for file in files:
        try:
            validate_image_file(file)
            
            # Check file size
            content = await file.read()
            if len(content) > settings.max_upload_size_bytes:
                errors.append(f"{file.filename}: File too large (max {settings.max_upload_size_mb}MB)")
                continue
            
            # Upload to storage
            import io
            result = await storage.upload_file(
                file=io.BytesIO(content),
                project_id=project.id,
                filename=file.filename,
                content_type=file.content_type or "image/jpeg",
            )
            
            # Create database record
            image = Image(
                project_id=project.id,
                storage_key=result["key"],
                original_filename=file.filename,
                content_type=file.content_type or "image/jpeg",
                size_bytes=result["size"],
            )
            db.add(image)
            uploaded_images.append(image)
            
        except HTTPException as e:
            errors.append(f"{file.filename}: {e.detail}")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    # Update project stats
    if uploaded_images:
        project.image_count += len(uploaded_images)
        project.total_size_bytes += sum(img.size_bytes for img in uploaded_images)
        
        if project.status == ProjectStatus.CREATED:
            project.status = ProjectStatus.UPLOADED
    
    await db.commit()
    
    # Refresh images to get IDs
    for img in uploaded_images:
        await db.refresh(img)
    
    return ImageUploadResponse(
        uploaded=len(uploaded_images),
        failed=len(errors),
        images=[ImageResponse.model_validate(img) for img in uploaded_images],
        errors=errors,
    )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(project: UserProject, image_id: int, db: DbSession):
    """Get image details."""
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.project_id == project.id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return image


@router.delete("/{image_id}", response_model=MessageResponse)
async def delete_image(project: UserProject, image_id: int, db: DbSession):
    """Delete an image."""
    if project.is_processing:
        raise HTTPException(status_code=400, detail="Cannot delete while processing")
    
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.project_id == project.id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete from storage
    await storage.delete_file(image.storage_key)
    
    # Update project stats
    project.image_count -= 1
    project.total_size_bytes -= image.size_bytes
    
    if project.image_count == 0:
        project.status = ProjectStatus.CREATED
    
    await db.delete(image)
    await db.commit()
    
    return MessageResponse(message="Image deleted")


@router.delete("", response_model=MessageResponse)
async def delete_all_images(project: UserProject, db: DbSession):
    """Delete all images from a project."""
    if project.is_processing:
        raise HTTPException(status_code=400, detail="Cannot delete while processing")
    
    # Delete from storage
    await storage.delete_folder(f"{project.storage_prefix}/images")
    
    # Delete from database
    result = await db.execute(
        select(Image).where(Image.project_id == project.id)
    )
    images = result.scalars().all()
    
    for image in images:
        await db.delete(image)
    
    # Reset project stats
    project.image_count = 0
    project.total_size_bytes = 0
    project.status = ProjectStatus.CREATED
    
    await db.commit()
    
    return MessageResponse(message=f"Deleted {len(images)} images")
