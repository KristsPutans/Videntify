"""Initial database schema

This migration creates the initial database schema for the VidID system.
"""

from datetime import datetime
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy import JSON, String


# Revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ENUMs, so we'll use string types with constraints instead
    # For a database-agnostic approach

    # Create videos table
    op.create_table(
        'videos',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('source', sa.String(50), nullable=False, index=True),
        sa.Column('content_type', sa.String(50), nullable=False, index=True),
        sa.Column('source_tier', sa.Integer, nullable=False, index=True),
        sa.Column('external_id', sa.String(255), nullable=True, index=True),
        sa.Column('duration', sa.Float, nullable=False),
        sa.Column('release_date', sa.DateTime, nullable=True, index=True),
        sa.Column('ingestion_date', sa.DateTime, default=datetime.utcnow, nullable=False, index=True),
        sa.Column('last_updated', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
        sa.Column('metadata', JSON, nullable=True)
    )
    
    # Create video_segments table
    op.create_table(
        'video_segments',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('video_id', String(36), sa.ForeignKey('videos.id'), nullable=False, index=True),
        sa.Column('start_time', sa.Float, nullable=False),
        sa.Column('end_time', sa.Float, nullable=False),
        sa.Column('duration', sa.Float, nullable=False),
        sa.Column('index', sa.Integer, nullable=False),
        sa.Column('key_frame_path', sa.String(512), nullable=True),
        sa.Column('metadata', JSON, nullable=True)
    )
    
    # Create video_features table
    op.create_table(
        'video_features',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('video_id', String(36), sa.ForeignKey('videos.id'), nullable=False, index=True),
        sa.Column('feature_type', sa.String(50), nullable=False, index=True),
        sa.Column('feature_vector_path', sa.String(512), nullable=True),
        sa.Column('feature_vector', sa.LargeBinary, nullable=True),
        sa.Column('feature_text', sa.Text, nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False)
    )
    
    # Create segment_features table
    op.create_table(
        'segment_features',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('segment_id', String(36), sa.ForeignKey('video_segments.id'), nullable=False, index=True),
        sa.Column('feature_type', sa.String(50), nullable=False, index=True),
        sa.Column('feature_vector_path', sa.String(512), nullable=True),
        sa.Column('feature_vector', sa.LargeBinary, nullable=True),
        sa.Column('feature_text', sa.Text, nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False)
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('username', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(512), nullable=False),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False),
        sa.Column('last_login', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_admin', sa.Boolean, default=False, nullable=False)
    )
    
    # Create queries table
    op.create_table(
        'queries',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('user_id', String(36), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('query_type', sa.String(50), nullable=False, index=True),
        sa.Column('query_data_path', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False, index=True),
        sa.Column('processing_time', sa.Float, nullable=True),
        sa.Column('success', sa.Boolean, nullable=True),
        sa.Column('client_info', JSON, nullable=True)
    )
    
    # Create query_results table
    op.create_table(
        'query_results',
        sa.Column('id', String(36), primary_key=True),
        sa.Column('query_id', String(36), sa.ForeignKey('queries.id'), nullable=False, index=True),
        sa.Column('video_id', String(36), sa.ForeignKey('videos.id'), nullable=False, index=True),
        sa.Column('segment_id', String(36), sa.ForeignKey('video_segments.id'), nullable=True, index=True),
        sa.Column('confidence', sa.Float, nullable=False, index=True),
        sa.Column('match_type', sa.String(50), nullable=False),
        sa.Column('rank', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False)
    )
    
    # Create basic indices (SQLite-compatible)
    op.create_index('idx_features_combined', 'video_features', ['video_id', 'feature_type'])
    op.create_index('idx_segment_features_combined', 'segment_features', ['segment_id', 'feature_type'])
    op.create_index('idx_query_results_confidence', 'query_results', ['confidence'])


def downgrade():
    # Drop all tables
    op.drop_table('query_results')
    op.drop_table('queries')
    op.drop_table('users')
    op.drop_table('segment_features')
    op.drop_table('video_features')
    op.drop_table('video_segments')
    op.drop_table('videos')
    
    # No enum types to drop in SQLite
