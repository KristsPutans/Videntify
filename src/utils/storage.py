"""Storage Utilities

This module provides utilities for managing object storage (files, videos, thumbnails, etc.)
"""

import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class ObjectStorage:
    """Base class for object storage implementations."""
    
    def upload_file(self, source_path: str, destination_path: str) -> bool:
        """Upload a file to storage.
        
        Args:
            source_path: Path to the local file
            destination_path: Path in storage
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def download_file(self, source_path: str, destination_path: str) -> bool:
        """Download a file from storage.
        
        Args:
            source_path: Path in storage
            destination_path: Path to download to
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from storage.
        
        Args:
            path: Path in storage
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_presigned_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for a file.
        
        Args:
            path: Path in storage
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL
        """
        raise NotImplementedError("Subclasses must implement this method")


class LocalObjectStorage(ObjectStorage):
    """Local file system object storage."""
    
    def __init__(self, base_dir: str):
        """Initialize local object storage.
        
        Args:
            base_dir: Base directory for storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized local object storage at {self.base_dir}")
    
    def upload_file(self, source_path: str, destination_path: str) -> bool:
        """Upload a file to local storage.
        
        Args:
            source_path: Path to the local file
            destination_path: Path in storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dest_path = self.base_dir / destination_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            logger.debug(f"Copied {source_path} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False
    
    def download_file(self, source_path: str, destination_path: str) -> bool:
        """Download a file from local storage.
        
        Args:
            source_path: Path in storage
            destination_path: Path to download to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = self.base_dir / source_path
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
            logger.debug(f"Copied {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from local storage.
        
        Args:
            path: Path in storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.base_dir / path
            if full_path.exists():
                full_path.unlink()
                logger.debug(f"Deleted {full_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def get_presigned_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a URL for a file in local storage.
        
        Args:
            path: Path in storage
            expires_in: Expiration time in seconds (not used for local storage)
            
        Returns:
            URL to the file
        """
        # For local storage, we just return a relative path that can be served by the web server
        return f"/storage/{path}"


class S3ObjectStorage(ObjectStorage):
    """AWS S3 object storage."""
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1', 
                 access_key: Optional[str] = None, secret_key: Optional[str] = None,
                 endpoint_url: Optional[str] = None):
        """Initialize S3 object storage.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key ID (or use environment variables)
            secret_key: AWS secret access key (or use environment variables)
            endpoint_url: Optional endpoint URL for S3-compatible services
        """
        self.bucket_name = bucket_name
        self.region = region
        self.endpoint_url = endpoint_url
        
        # Import boto3 here to avoid requiring it for all storage classes
        import boto3
        from botocore.exceptions import NoCredentialsError, PartialCredentialsError
        
        # Set up S3 client
        try:
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            self.s3_client = session.client('s3', endpoint_url=endpoint_url)
            
            # Ensure bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Initialized S3 object storage with bucket {bucket_name}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"S3 credential error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 storage: {str(e)}")
            raise
    
    def upload_file(self, source_path: str, destination_path: str) -> bool:
        """Upload a file to S3.
        
        Args:
            source_path: Path to the local file
            destination_path: Path in S3
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.upload_file(
                Filename=source_path,
                Bucket=self.bucket_name,
                Key=destination_path
            )
            logger.debug(f"Uploaded {source_path} to s3://{self.bucket_name}/{destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return False
    
    def download_file(self, source_path: str, destination_path: str) -> bool:
        """Download a file from S3.
        
        Args:
            source_path: Path in S3
            destination_path: Path to download to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=source_path,
                Filename=destination_path
            )
            logger.debug(f"Downloaded s3://{self.bucket_name}/{source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading from S3: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from S3.
        
        Args:
            path: Path in S3
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=path
            )
            logger.debug(f"Deleted s3://{self.bucket_name}/{path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from S3: {str(e)}")
            return False
    
    def get_presigned_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for an S3 object.
        
        Args:
            path: Path in S3
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': path
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return ""


class GCSObjectStorage(ObjectStorage):
    """Google Cloud Storage object storage."""
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None, 
                 credentials_path: Optional[str] = None):
        """Initialize Google Cloud Storage.
        
        Args:
            bucket_name: GCS bucket name
            project_id: Google Cloud project ID
            credentials_path: Path to service account credentials JSON file
        """
        self.bucket_name = bucket_name
        
        # Import google-cloud-storage here to avoid requiring it for all storage classes
        from google.cloud import storage
        from google.oauth2 import service_account
        
        # Set up credentials
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.storage_client = storage.Client(credentials=credentials, project=project_id)
        else:
            # Use default credentials (environment variables or instance service account)
            self.storage_client = storage.Client(project=project_id)
        
        # Get or create bucket
        try:
            self.bucket = self.storage_client.get_bucket(bucket_name)
            logger.info(f"Initialized GCS object storage with bucket {bucket_name}")
        except Exception as e:
            logger.error(f"Error initializing GCS storage: {str(e)}")
            raise
    
    def upload_file(self, source_path: str, destination_path: str) -> bool:
        """Upload a file to GCS.
        
        Args:
            source_path: Path to the local file
            destination_path: Path in GCS
            
        Returns:
            True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(source_path)
            logger.debug(f"Uploaded {source_path} to gs://{self.bucket_name}/{destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to GCS: {str(e)}")
            return False
    
    def download_file(self, source_path: str, destination_path: str) -> bool:
        """Download a file from GCS.
        
        Args:
            source_path: Path in GCS
            destination_path: Path to download to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            blob = self.bucket.blob(source_path)
            blob.download_to_filename(destination_path)
            logger.debug(f"Downloaded gs://{self.bucket_name}/{source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading from GCS: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from GCS.
        
        Args:
            path: Path in GCS
            
        Returns:
            True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(path)
            blob.delete()
            logger.debug(f"Deleted gs://{self.bucket_name}/{path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from GCS: {str(e)}")
            return False
    
    def get_presigned_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a signed URL for a GCS object.
        
        Args:
            path: Path in GCS
            expires_in: Expiration time in seconds
            
        Returns:
            Signed URL
        """
        try:
            blob = self.bucket.blob(path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=expires_in,
                method="GET"
            )
            return url
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            return ""


def create_storage(config: Dict[str, Any]) -> ObjectStorage:
    """Create an object storage instance based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Object storage instance
    """
    storage_type = config.get("storage_type", "local").lower()
    
    if storage_type == "local":
        storage_path = config.get("storage_path", "/tmp/vidid/storage")
        return LocalObjectStorage(storage_path)
    
    elif storage_type == "s3":
        bucket = config.get("s3_bucket", "vidid-content")
        region = config.get("s3_region", "us-east-1")
        access_key = config.get("s3_access_key")
        secret_key = config.get("s3_secret_key")
        endpoint_url = config.get("s3_endpoint_url")
        return S3ObjectStorage(bucket, region, access_key, secret_key, endpoint_url)
    
    elif storage_type == "gcs":
        bucket = config.get("gcs_bucket", "vidid-content")
        project_id = config.get("gcs_project_id")
        credentials_path = config.get("gcs_credentials_path")
        return GCSObjectStorage(bucket, project_id, credentials_path)
    
    else:
        logger.warning(f"Unknown storage type: {storage_type}, falling back to local storage")
        storage_path = config.get("storage_path", "/tmp/vidid/storage")
        return LocalObjectStorage(storage_path)
