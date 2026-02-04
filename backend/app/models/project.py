"""
Project model for PCI analysis projects.
"""
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.image import Image


class ProjectStatus(IntEnum):
    """Project processing status."""
    
    CREATED = 0       # Project created, no images
    UPLOADED = 1      # Images uploaded, ready for processing
    QUEUED = 2        # Processing queued
    PROCESSING = 3    # Currently processing
    COMPLETED = 4     # Processing completed successfully
    FAILED = 5        # Processing failed
    CANCELLED = 6     # Processing cancelled by user


class Project(Base):
    """
    PCI Analysis Project.
    Contains images and analysis results for a specific location.
    """
    
    __tablename__ = "projects"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Owner
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location (for geo-based queries)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[int] = mapped_column(
        Integer,
        default=ProjectStatus.CREATED,
        index=True,
    )
    
    # Processing Info
    task_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Results (flexible JSON storage)
    results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Computed PCI Score (also stored in results, but indexed for queries)
    pci_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    
    # Metadata
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    images: Mapped[list["Image"]] = relationship(
        "Image",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Image.created_at",
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_project_user_status", "user_id", "status"),
        Index("ix_project_user_created", "user_id", "created_at"),
        Index("ix_project_location", "latitude", "longitude"),
    )
    
    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.name}>"
    
    @property
    def status_name(self) -> str:
        """Human-readable status name."""
        return ProjectStatus(self.status).name
    
    @property
    def is_processing(self) -> bool:
        """Check if project is currently being processed."""
        return self.status in (ProjectStatus.QUEUED, ProjectStatus.PROCESSING)
    
    @property
    def can_process(self) -> bool:
        """Check if project can be submitted for processing."""
        return (
            self.status in (ProjectStatus.UPLOADED, ProjectStatus.FAILED, ProjectStatus.CANCELLED)
            and self.image_count > 0
        )
    
    @property
    def storage_prefix(self) -> str:
        """Storage path prefix for this project's files."""
        return f"projects/{self.id}"
