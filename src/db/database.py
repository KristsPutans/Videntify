"""Database Connection Module

This module handles connections to PostgreSQL, Vector DB, and Object Storage.
"""

import logging
from typing import Dict, Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()


class DatabaseManager:
    """Manager for database connections."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the database manager.
        
        Args:
            config: Configuration dictionary with database connection info
        """
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self.vector_db_client = None
        self.object_storage_client = None
        
        # Initialize connections
        self._init_metadata_db()
        self._init_vector_db()
        self._init_object_storage()
        
        logger.info("DatabaseManager initialized")
    
    def _init_metadata_db(self):
        """Initialize connection to the metadata database (PostgreSQL)."""
        db_config = self.config.get("metadata_db", {})
        db_url = db_config.get("url", "postgresql://postgres:postgres@localhost:5432/vidid")
        
        logger.info(f"Connecting to metadata database at {db_url}")
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _init_vector_db(self):
        """Initialize connection to the vector database (Milvus/Pinecone)."""
        vector_db_config = self.config.get("vector_db", {})
        vector_db_type = vector_db_config.get("type", "milvus")
        
        if vector_db_type.lower() == "milvus":
            try:
                # Import here to avoid dependency issues if Milvus is not installed
                from pymilvus import connections, utility
                
                host = vector_db_config.get("host", "localhost")
                port = vector_db_config.get("port", 19530)
                
                logger.info(f"Connecting to Milvus at {host}:{port}")
                connections.connect(host=host, port=port)
                self.vector_db_client = connections
                
            except ImportError:
                logger.error("pymilvus package not installed. Cannot connect to Milvus.")
                self.vector_db_client = None
                
        elif vector_db_type.lower() == "pinecone":
            try:
                # Import here to avoid dependency issues if Pinecone is not installed
                import pinecone
                
                api_key = vector_db_config.get("api_key")
                environment = vector_db_config.get("environment", "us-west1-gcp")
                
                if not api_key:
                    logger.error("Pinecone API key not provided. Cannot connect to Pinecone.")
                    self.vector_db_client = None
                    return
                
                logger.info(f"Connecting to Pinecone in environment {environment}")
                pinecone.init(api_key=api_key, environment=environment)
                self.vector_db_client = pinecone
                
            except ImportError:
                logger.error("pinecone-client package not installed. Cannot connect to Pinecone.")
                self.vector_db_client = None
        else:
            logger.error(f"Unsupported vector database type: {vector_db_type}")
            self.vector_db_client = None
    
    def _init_object_storage(self):
        """Initialize connection to object storage (S3, GCS, etc.)."""
        storage_config = self.config.get("object_storage", {})
        storage_type = storage_config.get("type", "s3")
        
        if storage_type.lower() == "s3":
            try:
                # Import here to avoid dependency issues if boto3 is not installed
                import boto3
                
                aws_access_key = storage_config.get("aws_access_key_id")
                aws_secret_key = storage_config.get("aws_secret_access_key")
                region = storage_config.get("region", "us-east-1")
                endpoint_url = storage_config.get("endpoint_url")  # For S3-compatible services
                
                logger.info(f"Connecting to S3 in region {region}")
                
                session = boto3.session.Session(
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=region
                )
                
                if endpoint_url:
                    self.object_storage_client = session.client('s3', endpoint_url=endpoint_url)
                else:
                    self.object_storage_client = session.client('s3')
                
            except ImportError:
                logger.error("boto3 package not installed. Cannot connect to S3.")
                self.object_storage_client = None
                
        elif storage_type.lower() == "gcs":
            try:
                # Import here to avoid dependency issues if GCS is not installed
                from google.cloud import storage
                
                credentials_path = storage_config.get("credentials_path")
                project_id = storage_config.get("project_id")
                
                logger.info(f"Connecting to Google Cloud Storage, project: {project_id}")
                
                if credentials_path:
                    self.object_storage_client = storage.Client.from_service_account_json(
                        credentials_path, project=project_id)
                else:
                    self.object_storage_client = storage.Client(project=project_id)
                
            except ImportError:
                logger.error("google-cloud-storage package not installed. Cannot connect to GCS.")
                self.object_storage_client = None
        else:
            logger.error(f"Unsupported object storage type: {storage_type}")
            self.object_storage_client = None
    
    def get_db_session(self) -> Session:
        """Get a database session for the metadata database.
        
        Returns:
            SQLAlchemy Session object
        """
        if not self.SessionLocal:
            raise ValueError("Metadata database not initialized")
            
        db = self.SessionLocal()
        try:
            return db
        finally:
            db.close()
    
    def get_vector_db_client(self):
        """Get the vector database client.
        
        Returns:
            Vector database client (type depends on the configured database)
        """
        if not self.vector_db_client:
            raise ValueError("Vector database not initialized")
            
        return self.vector_db_client
    
    def get_object_storage_client(self):
        """Get the object storage client.
        
        Returns:
            Object storage client (type depends on the configured storage)
        """
        if not self.object_storage_client:
            raise ValueError("Object storage not initialized")
            
        return self.object_storage_client
    
    def create_tables(self):
        """Create all tables in the metadata database."""
        from src.db.models import Base  # Import here to avoid circular imports
        
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=self.engine)
        
    def create_vector_collections(self):
        """Create collections in the vector database."""
        vector_db_config = self.config.get("vector_db", {})
        vector_db_type = vector_db_config.get("type", "milvus")
        
        if not self.vector_db_client:
            logger.error("Vector database client not initialized, cannot create collections")
            return
        
        logger.info("Creating vector database collections")
        
        # Example for Milvus
        if vector_db_type.lower() == "milvus":
            try:
                from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
                
                # Define collection for CNN features
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                    FieldSchema(name="video_id", dtype=DataType.VARCHAR, max_length=36),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=2048)  # ResNet features
                ]
                schema = CollectionSchema(fields, "CNN features collection")
                cnn_collection = Collection("cnn_features", schema)
                
                # Define collection for perceptual hashes
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                    FieldSchema(name="video_id", dtype=DataType.VARCHAR, max_length=36),
                    FieldSchema(name="hash", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(name="timestamp", dtype=DataType.FLOAT)
                ]
                schema = CollectionSchema(fields, "Perceptual hash collection")
                hash_collection = Collection("perceptual_hashes", schema)
                
                logger.info("Created vector database collections successfully")
                
            except Exception as e:
                logger.error(f"Error creating Milvus collections: {e}")
        
        # Example for Pinecone
        elif vector_db_type.lower() == "pinecone":
            try:
                # Create index for CNN features
                self.vector_db_client.create_index(
                    name="cnn-features",
                    dimension=2048,  # ResNet features
                    metric="cosine"
                )
                
                logger.info("Created Pinecone indexes successfully")
                
            except Exception as e:
                logger.error(f"Error creating Pinecone indexes: {e}")
