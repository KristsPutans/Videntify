"""Configuration Module

This module handles configuration loading and management for the VidID system.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
        "debug": False,
        "workers": 4,
        "cors_origins": ["*"]
    },
    "metadata_db": {
        "url": "postgresql://postgres:postgres@localhost:5432/vidid",
        "pool_size": 20,
        "max_overflow": 10
    },
    "vector_db": {
        "type": "milvus",  # milvus or pinecone
        "host": "localhost",
        "port": 19530,
        "api_key": "",  # For Pinecone
        "environment": ""  # For Pinecone
    },
    "object_storage": {
        "type": "s3",  # s3 or gcs
        "bucket": "vidid-content",
        "aws_access_key_id": "",
        "aws_secret_access_key": "",
        "region": "us-east-1",
        "endpoint_url": "",  # For S3-compatible services
        "credentials_path": "",  # For GCS
        "project_id": ""  # For GCS
    },
    "feature_extraction": {
        "gpu_enabled": True,
        "batch_size": 32,
        "model_path": "models/resnet50.pth",
        "scene_detection_threshold": 30.0
    },
    "matching": {
        "match_threshold": 0.85,
        "default_top_k": 5,
        "temporal_alignment_enabled": True
    },
    "indexing": {
        "sharding_strategy": "content_based",  # content_based, geographic, or tiered
        "reindex_interval_hours": 24,
        "max_cache_size_gb": 10.0
    },
    "query_processing": {
        "temp_dir": "/tmp",
        "max_clip_duration_seconds": 60,
        "preprocessing_enabled": True
    },
    "content_acquisition": {
        "api_keys": {
            "youtube": "",
            "netflix": "",
            "disney": ""
        },
        "batch_size": 50,
        "max_concurrent_downloads": 10
    },
    "logging": {
        "level": "INFO",
        "file": "logs/vidid.log",
        "max_size_mb": 100,
        "backup_count": 10
    }
}


class ConfigManager:
    """Manager for loading and accessing configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file (JSON format)
        """
        self.config = DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load_config(config_path)
        
        # Override with environment variables
        self._override_from_env()
        
        logger.info("Configuration loaded successfully")
    
    def load_config(self, config_path: str) -> bool:
        """Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            True if loading was successful, False otherwise
        """
        try:
            if not os.path.exists(config_path):
                logger.warning(f"Configuration file not found: {config_path}")
                return False
                
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                
            # Recursively update the configuration
            self._update_config(self.config, file_config)
            
            logger.info(f"Loaded configuration from {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def _update_config(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Recursively update a nested dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value)
            else:
                target[key] = value
    
    def _override_from_env(self):
        """Override configuration with environment variables."""
        # Database URL
        if 'VIDID_DB_URL' in os.environ:
            self.config['metadata_db']['url'] = os.environ['VIDID_DB_URL']
            
        # Vector DB
        if 'VIDID_VECTOR_DB_HOST' in os.environ:
            self.config['vector_db']['host'] = os.environ['VIDID_VECTOR_DB_HOST']
            
        if 'VIDID_VECTOR_DB_PORT' in os.environ:
            self.config['vector_db']['port'] = int(os.environ['VIDID_VECTOR_DB_PORT'])
            
        if 'VIDID_VECTOR_DB_API_KEY' in os.environ:
            self.config['vector_db']['api_key'] = os.environ['VIDID_VECTOR_DB_API_KEY']
            
        # S3 credentials
        if 'AWS_ACCESS_KEY_ID' in os.environ:
            self.config['object_storage']['aws_access_key_id'] = os.environ['AWS_ACCESS_KEY_ID']
            
        if 'AWS_SECRET_ACCESS_KEY' in os.environ:
            self.config['object_storage']['aws_secret_access_key'] = os.environ['AWS_SECRET_ACCESS_KEY']
            
        # API settings
        if 'VIDID_API_PORT' in os.environ:
            self.config['api']['port'] = int(os.environ['VIDID_API_PORT'])
            
        if 'VIDID_DEBUG' in os.environ:
            self.config['api']['debug'] = os.environ['VIDID_DEBUG'].lower() == 'true'
            
        # Logging level
        if 'VIDID_LOG_LEVEL' in os.environ:
            self.config['logging']['level'] = os.environ['VIDID_LOG_LEVEL']
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get a configuration value by path.
        
        Args:
            path: Path to the configuration value (e.g., 'api.port')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def set(self, path: str, value: Any):
        """Set a configuration value by path.
        
        Args:
            path: Path to the configuration value (e.g., 'api.port')
            value: Value to set
        """
        keys = path.split('.')
        target = self.config
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
                
        target[keys[-1]] = value
        
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration.
        
        Returns:
            Dictionary with all configuration values
        """
        return self.config.copy()
    
    def save(self, config_path: str) -> bool:
        """Save the current configuration to a file.
        
        Args:
            config_path: Path to save the configuration file
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.info(f"Saved configuration to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
