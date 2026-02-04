"""
Application configuration using Pydantic Settings.
Loads from environment variables with sensible defaults.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Application
    # ==========================================================================
    app_name: str = "PCI Platform"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=True)
    secret_key: str = Field(default="change-me-in-production")

    # API Settings
    api_v1_prefix: str = "/api/v1"

    # ==========================================================================
    # Database
    # ==========================================================================
    database_url: str = Field(
        default="postgresql+asyncpg://pci:pci_secret@localhost:5432/pci_db"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")

    # ==========================================================================
    # Redis
    # ==========================================================================
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ==========================================================================
    # Celery
    # ==========================================================================
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # ==========================================================================
    # MinIO / S3
    # ==========================================================================
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_bucket: str = Field(default="pci-images")
    minio_secure: bool = Field(default=False)

    @computed_field
    @property
    def minio_public_url(self) -> str:
        """Public URL for accessing MinIO objects."""
        protocol = "https" if self.minio_secure else "http"
        return f"{protocol}://{self.minio_endpoint}/{self.minio_bucket}"

    # ==========================================================================
    # Authentication
    # ==========================================================================
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # ==========================================================================
    # ML Models
    # ==========================================================================
    ml_detection_model_path: str = Field(default="/app/ml/models/detection.pt")
    ml_segmentation_model_path: str = Field(default="/app/ml/models/segmentation.pth")
    ml_device: str = Field(default="cpu")  # "cpu" or "cuda"

    # ==========================================================================
    # File Upload
    # ==========================================================================
    max_upload_size_mb: int = 50
    allowed_image_extensions: set[str] = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

    @computed_field
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ==========================================================================
    # CORS
    # ==========================================================================
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # ==========================================================================
    # Logging
    # ==========================================================================
    log_level: str = Field(default="INFO")
    log_format: Literal["json", "console"] = "console"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
