from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to find our modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from src.config.config import ConfigManager

# Alembic Config object
config = context.config

# Load our config
config_manager = ConfigManager()
db_url = config_manager.get('metadata_db.url')

# Override alembic.ini sqlalchemy.url with our config
config.set_main_option('sqlalchemy.url', db_url)

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Define the MetaData object
# This is empty since we're using SQLAlchemy's declarative API
# Models will be loaded at runtime
target_metadata = None


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
