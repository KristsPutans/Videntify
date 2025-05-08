"""VidID Main Application

Main entry point for the VidID video identification system.
"""

import os
import sys
import argparse
import logging
import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to path
src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from config.config import ConfigManager
from core.feature_extraction import FeatureExtractionEngine
from core.matching_engine import MatchingEngine
from core.indexing_system import IndexingSystem
from core.query_processing import QueryProcessingEngine
from db.database import DatabaseManager
from api.api import app as api_app
from web.admin_dashboard import router as admin_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_services(config_manager):
    """Initialize all services required by the VidID system.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        Dictionary of initialized services
    """
    config = config_manager.get_all()
    
    # Initialize database manager
    logger.info("Initializing database manager")
    db_manager = DatabaseManager(config)
    
    # Create database tables if they don't exist
    db_manager.create_tables()
    
    # Initialize vector collections if needed
    db_manager.create_vector_collections()
    
    # Initialize feature extraction engine
    logger.info("Initializing feature extraction engine")
    feature_engine = FeatureExtractionEngine(config.get("feature_extraction", {}))
    
    # Initialize matching engine
    logger.info("Initializing matching engine")
    matching_engine = MatchingEngine(
        config.get("matching", {}),
        db_manager.vector_db_client,
        db_manager.get_db_session
    )
    
    # Initialize indexing system
    logger.info("Initializing indexing system")
    indexing_system = IndexingSystem(
        config.get("indexing", {}),
        db_manager.vector_db_client,
        db_manager.get_db_session
    )
    
    # Initialize query processing engine
    logger.info("Initializing query processing engine")
    query_engine = QueryProcessingEngine(
        config.get("query_processing", {}),
        feature_engine,
        matching_engine
    )
    
    return {
        "db_manager": db_manager,
        "feature_engine": feature_engine,
        "matching_engine": matching_engine,
        "indexing_system": indexing_system,
        "query_engine": query_engine
    }


def create_app(services):
    """Create and configure the FastAPI application.
    
    Args:
        services: Dictionary of initialized services
        
    Returns:
        Configured FastAPI application
    """
    # Set up dependencies in the API app
    api_app.state.db_manager = services["db_manager"]
    api_app.state.feature_engine = services["feature_engine"]
    api_app.state.matching_engine = services["matching_engine"]
    api_app.state.query_engine = services["query_engine"]
    
    # Add admin dashboard routers
    api_app.include_router(admin_router)
    
    return api_app


async def start_services(services, config_manager):
    """Start background services.
    
    Args:
        services: Dictionary of initialized services
        config_manager: Configuration manager instance
    """
    # This would start any background services
    # For example, periodic reindexing, content acquisition, etc.
    pass


async def main(config_path=None):
    """Main entry point for the VidID system.
    
    Args:
        config_path: Path to the configuration file
    """
    # Load configuration
    config_manager = ConfigManager(config_path)
    
    # Initialize services
    services = await initialize_services(config_manager)
    
    # Create FastAPI app
    app = create_app(services)
    
    # Start background services
    asyncio.create_task(start_services(services, config_manager))
    
    # Configure API server settings
    api_config = config_manager.get("api", {})
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8000)
    debug = api_config.get("debug", False)
    
    # Run API server
    logger.info(f"Starting VidID API on {host}:{port} (debug: {debug})")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VidID Video Identification System")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Run the main function
    asyncio.run(main(args.config))
