"""
Object storage service using MinIO/S3.
Handles file uploads, downloads, and management.
"""
import io
import uuid
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error

from app.config import settings


class StorageService:
    """
    S3-compatible object storage service.
    Works with MinIO (local) or AWS S3 (production).
    """
    
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
    
    async def health_check(self) -> bool:
        """Check if storage is accessible."""
        try:
            self.client.bucket_exists(self.bucket)
            return True
        except Exception:
            return False
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
    
    def _generate_key(
        self,
        project_id: int,
        filename: str,
        folder: str = "images",
    ) -> str:
        """
        Generate unique storage key.
        Format: projects/{project_id}/{folder}/{uuid}_{filename}
        """
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = Path(filename).name  # Remove any path components
        return f"projects/{project_id}/{folder}/{unique_id}_{safe_filename}"
    
    async def upload_file(
        self,
        file: BinaryIO,
        project_id: int,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "images",
    ) -> dict:
        """
        Upload a file to object storage.
        
        Returns:
            dict with 'key' and 'url'
        """
        self._ensure_bucket()
        
        key = self._generate_key(project_id, filename, folder)
        
        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=file,
                length=file_size,
                content_type=content_type,
            )
            
            return {
                "key": key,
                "url": self.get_public_url(key),
                "size": file_size,
            }
        except S3Error as e:
            raise StorageError(f"Failed to upload file: {e}")
    
    async def upload_bytes(
        self,
        data: bytes,
        project_id: int,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "images",
    ) -> dict:
        """Upload bytes directly to storage."""
        file = io.BytesIO(data)
        return await self.upload_file(
            file=file,
            project_id=project_id,
            filename=filename,
            content_type=content_type,
            folder=folder,
        )
    
    async def download_file(self, key: str) -> bytes:
        """Download file from storage."""
        try:
            response = self.client.get_object(self.bucket, key)
            return response.read()
        except S3Error as e:
            raise StorageError(f"Failed to download file: {e}")
        finally:
            response.close()
            response.release_conn()
    
    async def delete_file(self, key: str) -> bool:
        """Delete a file from storage."""
        try:
            self.client.remove_object(self.bucket, key)
            return True
        except S3Error:
            return False
    
    async def delete_folder(self, prefix: str) -> int:
        """
        Delete all files with a given prefix (folder).
        Returns count of deleted files.
        """
        deleted = 0
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix, recursive=True)
            for obj in objects:
                self.client.remove_object(self.bucket, obj.object_name)
                deleted += 1
        except S3Error as e:
            raise StorageError(f"Failed to delete folder: {e}")
        
        return deleted
    
    async def list_files(
        self,
        project_id: int,
        folder: str = "images",
    ) -> list[dict]:
        """List all files in a project folder."""
        prefix = f"projects/{project_id}/{folder}/"
        
        try:
            objects = self.client.list_objects(
                self.bucket,
                prefix=prefix,
                recursive=True,
            )
            
            return [
                {
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "url": self.get_public_url(obj.object_name),
                }
                for obj in objects
            ]
        except S3Error as e:
            raise StorageError(f"Failed to list files: {e}")
    
    def get_public_url(self, key: str) -> str:
        """Get public URL for a file."""
        return f"{settings.minio_public_url}/{key}"
    
    def get_presigned_url(
        self,
        key: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """
        Get a presigned URL for temporary access.
        Useful for private files.
        """
        return self.client.presigned_get_object(
            self.bucket,
            key,
            expires=expires,
        )
    
    def get_presigned_upload_url(
        self,
        key: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """
        Get a presigned URL for direct upload.
        Enables client-side uploads without going through the API.
        """
        return self.client.presigned_put_object(
            self.bucket,
            key,
            expires=expires,
        )


class StorageError(Exception):
    """Storage operation error."""
    pass


# Global storage instance
storage = StorageService()
