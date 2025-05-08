"""Migration Manager

This module manages database migrations for the VidID system.
"""

import os
import sys
import logging
import argparse
from importlib import import_module
from pathlib import Path
from datetime import datetime

import alembic
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.config.config import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migration-manager")


class MigrationManager:
    """Manager for database migrations."""
    
    def __init__(self, config_path=None):
        """Initialize the migration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_all()
        # Force SQLite for development (override any config)
        self.db_url = "sqlite:///vidid.db"
        print(f"DEBUG: Using database URL: {self.db_url}")
        self.migrations_dir = Path(__file__).parent / 'migrations'
        
        # Set up Alembic config
        self.alembic_cfg = Config()
        self.alembic_cfg.set_main_option('script_location', str(self.migrations_dir))
        self.alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)
        
        # Create engine
        self.engine = create_engine(self.db_url)
        
    def check_db_connection(self):
        """Check database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Handle SQLite connections differently
            if self.db_url.startswith('sqlite'):
                # For SQLite, we just need to check if the file can be created/accessed
                # Extract the SQLite filepath from the URL
                sqlite_path = self.db_url.replace('sqlite:///', '')
                # For in-memory SQLite or other special cases
                if not sqlite_path or sqlite_path == ':memory:':
                    return True
                    
                # For file-based SQLite
                directory = os.path.dirname(sqlite_path) if os.path.dirname(sqlite_path) else '.'
                if not os.path.exists(directory):
                    os.makedirs(directory)
                return True
            else:
                # For other database types like PostgreSQL
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def create_migration(self, name):
        """Create a new migration.
        
        Args:
            name: Name of the migration
            
        Returns:
            Path to the created migration file
        """
        # Find the highest revision number
        highest_rev = 0
        for migration_file in self.migrations_dir.glob('*.py'):
            if migration_file.stem.startswith('0'):
                try:
                    rev_num = int(migration_file.stem.split('_')[0])
                    highest_rev = max(highest_rev, rev_num)
                except (ValueError, IndexError):
                    pass
        
        # Create new revision number
        new_rev = highest_rev + 1
        rev_str = f"{new_rev:03d}"
        
        # Create new migration file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{rev_str}_{timestamp}_{name}.py"
        file_path = self.migrations_dir / file_name
        
        # Determine down_revision based on highest_rev
        down_rev = f"'{highest_rev:03d}'" if highest_rev > 0 else 'None'
        
        # Create a simple migration template as a raw string
        template = '''
# Migration: {name}
# 
# Created: {timestamp}

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy.dialects import sqlite, postgresql


# Revision identifiers used by Alembic
revision = '{rev_str}'
down_revision = {down_rev}
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema."""
    # Add your upgrade operations here
    pass


def downgrade():
    """Downgrade database schema."""
    # Add your downgrade operations here
    pass
'''
        
        # Format the template with the values
        migration_template = template.format(
            name=name,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            rev_str=rev_str,
            down_rev=down_rev
        )
        
        # Write template to file
        with open(file_path, 'w') as f:
            f.write(migration_template)
        
        logger.info(f"Created migration: {file_path}")
        return file_path
    
    def run_migrations(self, target='head'):
        """Run migrations to the specified target.
        
        Args:
            target: Migration target (revision identifier or 'head')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Running migrations to target: {target}")
            command.upgrade(self.alembic_cfg, target)
            logger.info("Migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            return False
    
    def rollback_migration(self, target):
        """Rollback migrations to the specified target.
        
        Args:
            target: Migration target to rollback to (revision identifier or '-1' for one step back)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Rolling back migrations to target: {target}")
            command.downgrade(self.alembic_cfg, target)
            logger.info("Rollback completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error rolling back migrations: {e}")
            return False
    
    def get_migration_history(self):
        """Get migration history.
        
        Returns:
            List of applied migrations
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version_num, timestamp FROM alembic_version_history ORDER BY timestamp DESC"))
                return [dict(row) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Error getting migration history: {e}")
            return []
    
    def get_current_revision(self):
        """Get current revision.
        
        Returns:
            Current revision identifier
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                row = result.fetchone()
                return row[0] if row else None
        except SQLAlchemyError as e:
            logger.error(f"Error getting current revision: {e}")
            return None


def main():
    """Main entry point for the migration manager."""
    parser = argparse.ArgumentParser(description="VidID Database Migration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("name", help="Name of the migration")
    
    # Run migrations command
    run_parser = subparsers.add_parser("run", help="Run migrations")
    run_parser.add_argument("--target", default="head", help="Migration target (default: head)")
    
    # Rollback migrations command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migrations")
    rollback_parser.add_argument("target", help="Target to rollback to (revision or '-1' for one step)")
    
    # History command
    subparsers.add_parser("history", help="Show migration history")
    
    # Current command
    subparsers.add_parser("current", help="Show current revision")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Use custom config file")
    config_parser.add_argument("--path", required=True, help="Path to config file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize migration manager
    manager = MigrationManager()
    
    # Check database connection
    if not manager.check_db_connection():
        logger.error("Failed to connect to database. Check configuration.")
        return 1
    
    # Execute command
    if args.command == "create":
        manager.create_migration(args.name)
        
    elif args.command == "run":
        # Run migrations to the head or specified target
        target = getattr(args, 'target', 'head')
        success = manager.run_migrations(target)
        return 0 if success else 1
        
    elif args.command == "rollback":
        success = manager.rollback_migration(args.target)
        return 0 if success else 1
        
    elif args.command == "history":
        history = manager.get_migration_history()
        if history:
            print("\nMigration History:")
            for entry in history:
                print(f"  {entry['version_num']} - {entry['timestamp']}")
        else:
            print("No migration history found")
            
    elif args.command == "current":
        current = manager.get_current_revision()
        if current:
            print(f"\nCurrent revision: {current}")
        else:
            print("No current revision found")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
