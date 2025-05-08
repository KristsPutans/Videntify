"""Database Initialization Script

This script initializes the SQLite database using SQLAlchemy models.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to find our modules
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from sqlalchemy import create_engine
from src.db.models import Base
from src.config.config import ConfigManager


def init_db(db_url=None):
    """Initialize the database with all tables defined in models.py.
    
    Args:
        db_url: Optional database URL, defaults to the one in config
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use provided URL or get from config
        if db_url is None:
            config_manager = ConfigManager()
            db_url = config_manager.get('metadata_db.url')
            
        # Force SQLite for development (remove this in production)
        db_url = "sqlite:///vidid.db"
        
        print(f"Initializing database with URL: {db_url}")
        
        # Create engine and tables
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        
        print("Database initialization completed successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    init_db()
