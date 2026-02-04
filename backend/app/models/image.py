"""
Image model for project images.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Image(Base):
    """
    Project image stored in object storage.
    Contains metadata and analysis results for individual images.
    """
    
    __tablename__ = "images"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Parent Project
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    
    # Storage Info
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), default="image/jpeg")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Image Metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Analysis Results (per-image)
    analysis_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Result files (segmentation masks, annotated images, etc.)
    result_keys: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Example: {"mask": "projects/1/results/img1_mask.png", "annotated": "..."}
    
    # Processing Status
    processed: Mapped[bool] = mapped_column(default=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="images")
    
    # Indexes
    __table_args__ = (
        Index("ix_image_project_created", "project_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Image {self.id}: {self.original_filename}>"
    
    @property
    def url(self) -> str:
        """Public URL for this image."""
        from app.config import settings
        return f"{settings.minio_public_url}/{self.storage_key}"
