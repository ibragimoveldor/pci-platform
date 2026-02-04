"""PCI Analysis endpoints - triggers async processing."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from celery.result import AsyncResult

from app.api.deps import DbSession, UserProject
from app.models import ProjectStatus
from app.schemas import (
    AnalysisStartResponse,
    AnalysisStatusResponse,
    MessageResponse,
)
from app.workers.celery_app import celery_app

router = APIRouter()


@router.post("/start", response_model=AnalysisStartResponse)
async def start_analysis(project: UserProject, db: DbSession):
    """
    Start PCI analysis for a project.
    This queues a background task and returns immediately.
    """
    if not project.can_process:
        if project.is_processing:
            raise HTTPException(
                status_code=400,
                detail="Analysis already in progress",
            )
        if project.image_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No images to analyze. Upload images first.",
            )
        raise HTTPException(
            status_code=400,
            detail="Project cannot be processed in current state",
        )
    
    # Import task here to avoid circular imports
    from app.workers.tasks.analysis import process_project_task
    
    # Queue the task
    task = process_project_task.delay(project.id)
    
    # Update project status
    project.status = ProjectStatus.QUEUED
    project.task_id = task.id
    project.processing_started_at = datetime.now(timezone.utc)
    project.processing_completed_at = None
    project.processing_error = None
    
    await db.commit()
    
    return AnalysisStartResponse(
        project_id=project.id,
        task_id=task.id,
        status="queued",
        message="Analysis queued successfully",
    )


@router.get("/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(project: UserProject):
    """Get current analysis status for a project."""
    if not project.task_id:
        return AnalysisStatusResponse(
            task_id="",
            status="not_started",
            progress=0,
            message="No analysis has been started",
        )
    
    # Check Celery task status
    task_result = AsyncResult(project.task_id, app=celery_app)
    
    status_map = {
        "PENDING": ("queued", 0, "Waiting in queue"),
        "STARTED": ("processing", 10, "Analysis started"),
        "PROGRESS": ("processing", 0, "Processing"),  # Progress updated from task info
        "SUCCESS": ("completed", 100, "Analysis completed"),
        "FAILURE": ("failed", 0, "Analysis failed"),
        "REVOKED": ("cancelled", 0, "Analysis cancelled"),
    }
    
    celery_status = task_result.status
    status_info = status_map.get(celery_status, ("unknown", 0, celery_status))
    
    progress = status_info[1]
    message = status_info[2]
    result = None
    
    # Get progress info from task state
    if celery_status == "PROGRESS" and task_result.info:
        progress = task_result.info.get("progress", 0)
        message = task_result.info.get("message", "Processing")
    elif celery_status == "SUCCESS":
        result = task_result.result
    elif celery_status == "FAILURE":
        message = str(task_result.result) if task_result.result else "Unknown error"
    
    return AnalysisStatusResponse(
        task_id=project.task_id,
        status=status_info[0],
        progress=progress,
        message=message,
        result=result,
    )


@router.post("/cancel", response_model=MessageResponse)
async def cancel_analysis(project: UserProject, db: DbSession):
    """Cancel ongoing analysis."""
    if not project.is_processing:
        raise HTTPException(
            status_code=400,
            detail="No analysis in progress",
        )
    
    if project.task_id:
        celery_app.control.revoke(project.task_id, terminate=True)
    
    project.status = ProjectStatus.CANCELLED
    project.processing_completed_at = datetime.now(timezone.utc)
    project.processing_error = "Cancelled by user"
    
    await db.commit()
    
    return MessageResponse(message="Analysis cancelled")


@router.get("/results")
async def get_analysis_results(project: UserProject):
    """Get analysis results for a completed project."""
    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Analysis not completed",
        )
    
    return {
        "project_id": project.id,
        "pci_score": project.pci_score,
        "results": project.results,
        "processing_time_seconds": (
            (project.processing_completed_at - project.processing_started_at).total_seconds()
            if project.processing_started_at and project.processing_completed_at
            else None
        ),
    }
