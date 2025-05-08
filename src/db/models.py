"""Database Models

This module defines the database models for storing video data, features, and metadata.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Enum as SQLEnum, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ContentSourceEnum(str, Enum):
    """Enum representing different content sources."""
    STREAMING = "streaming"  # Netflix, Disney+, etc.
    TELEVISION = "television"  # Network television
    YOUTUBE = "youtube"  # YouTube content
    ARCHIVE = "archive"  # Archive content
    USER = "user"  # User-submitted content
    UNKNOWN = "unknown"  # Unknown source


class ContentTypeEnum(str, Enum):
    """Enum representing different content types."""
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    TV_EPISODE = "tv_episode"
    SHORT = "short"
    CLIP = "clip"
    TRAILER = "trailer"
    USER_GENERATED = "user_generated"


class SourceTierEnum(int, Enum):
    """Tier classification for content sources."""
    TIER_1 = 1  # Popular streaming platforms top 10,000 titles
    TIER_2 = 2  # Network television shows (current season)
    TIER_3 = 3  # YouTube trending content and channels >1M subscribers
    TIER_4 = 4  # Archive content based on popularity metrics


class Video(Base):
    """Model for video content."""
    __tablename__ = "videos"
    
    id = Column(String(36), primary_key=True)  # UUID
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(255), nullable=True)  # MIME type
    size_bytes = Column(Integer, nullable=False, default=0)
    duration = Column(Float, nullable=True)
    source = Column(SQLEnum(ContentSourceEnum), nullable=False, default=ContentSourceEnum.UNKNOWN, index=True)
    source_id = Column(String(255), nullable=True, index=True)  # ID in the source system
    tags = Column(JSON, nullable=True, default=list)  # List of tags
    custom_meta_data = Column(JSON, nullable=True, default=dict)  # Additional metadata as JSON
    
    # Storage information
    storage_path = Column(String(512), nullable=True)  # Path in storage
    thumbnail_path = Column(String(512), nullable=True)  # Path to thumbnail
    
    # Feature extraction status
    status = Column(String(50), nullable=False, default="uploaded", index=True)  # uploaded, processing, ready, error
    feature_extraction_status = Column(String(50), nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    features_extracted = Column(JSON, nullable=True)  # List of extracted feature types
    
    # Access control
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # Owner of the video
    is_public = Column(Boolean, default=False, nullable=False, index=True)  # Whether the video is publicly accessible
    
    # Timestamps
    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    release_date = Column(DateTime, nullable=True, index=True)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # External system information
    content_category = Column(SQLEnum(ContentTypeEnum), nullable=True, index=True)
    source_tier = Column(SQLEnum(SourceTierEnum), nullable=True, index=True)
    external_id = Column(String(255), nullable=True, index=True)  # ID in external system
    
    # Relationships
    segments = relationship("VideoSegment", back_populates="video")
    features = relationship("VideoFeature", back_populates="video")
    user = relationship("User", back_populates="videos")
    
    def __repr__(self):
        return f"<Video(id='{self.id}', title='{self.title}', status='{self.status}')>"


class VideoSegment(Base):
    """Model for video segments (scenes)."""
    __tablename__ = "video_segments"
    
    id = Column(String(36), primary_key=True)  # UUID
    video_id = Column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)  # End time in seconds
    duration = Column(Float, nullable=False)  # Duration in seconds
    index = Column(Integer, nullable=False)  # Segment index in the video
    key_frame_path = Column(String(512), nullable=True)  # Path to key frame image
    meta_data = Column(JSON, nullable=True)  # Additional metadata as JSON
    
    # Relationships
    video = relationship("Video", back_populates="segments")
    features = relationship("SegmentFeature", back_populates="segment")
    
    def __repr__(self):
        return f"<VideoSegment(id='{self.id}', video_id='{self.video_id}', start={self.start_time:.2f}, end={self.end_time:.2f})>"


class FeatureTypeEnum(str, Enum):
    """Types of features that can be extracted from videos."""
    PERCEPTUAL_HASH = "perceptual_hash"  # Perceptual hash for frames
    CNN_FEATURES = "cnn_features"  # CNN-extracted features
    SCENE_TRANSITION = "scene_transition"  # Scene transition features
    MOTION_PATTERN = "motion_pattern"  # Motion pattern features
    AUDIO_SPECTROGRAM = "audio_spectrogram"  # Audio spectrogram features
    AUDIO_TRANSCRIPT = "audio_transcript"  # Audio transcript


class VideoFeature(Base):
    """Model for video-level features."""
    __tablename__ = "video_features"
    
    id = Column(String(36), primary_key=True)  # UUID
    video_id = Column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    feature_type = Column(SQLEnum(FeatureTypeEnum), nullable=False, index=True)
    feature_vector_path = Column(String(512), nullable=True)  # Path to feature vector file
    feature_vector = Column(LargeBinary, nullable=True)  # Binary feature vector (for small vectors)
    feature_text = Column(Text, nullable=True)  # Text feature (for hashes, transcripts)
    meta_data = Column(JSON, nullable=True)  # Additional metadata as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    video = relationship("Video", back_populates="features")
    
    def __repr__(self):
        return f"<VideoFeature(id='{self.id}', video_id='{self.video_id}', type='{self.feature_type}')>"


class SegmentFeature(Base):
    """Model for segment-level features."""
    __tablename__ = "segment_features"
    
    id = Column(String(36), primary_key=True)  # UUID
    segment_id = Column(String(36), ForeignKey("video_segments.id"), nullable=False, index=True)
    feature_type = Column(SQLEnum(FeatureTypeEnum), nullable=False, index=True)
    feature_vector_path = Column(String(512), nullable=True)  # Path to feature vector file
    feature_vector = Column(LargeBinary, nullable=True)  # Binary feature vector (for small vectors)
    feature_text = Column(Text, nullable=True)  # Text feature (for hashes, transcripts)
    meta_data = Column(JSON, nullable=True)  # Additional metadata as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    segment = relationship("VideoSegment", back_populates="features")
    
    def __repr__(self):
        return f"<SegmentFeature(id='{self.id}', segment_id='{self.segment_id}', type='{self.feature_type}')>"


class User(Base):
    """Model for user information."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)  # UUID
    username = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(512), nullable=False)
    full_name = Column(String(255), nullable=True)
    profile_image_path = Column(String(512), nullable=True)
    preferences = Column(JSON, nullable=True)  # User preferences as JSON
    
    # Authentication and status
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    api_key = Column(String(512), nullable=True, unique=True)  # For API access
    
    # Account details
    account_type = Column(String(50), default="free", nullable=False)  # free, premium, enterprise
    subscription_expires = Column(DateTime, nullable=True)
    quota_limit = Column(Integer, default=100, nullable=False)  # Queries per month
    quota_used = Column(Integer, default=0, nullable=False)  # Queries used this month
    quota_reset_date = Column(DateTime, nullable=True)
    
    # Relationships
    queries = relationship("Query", back_populates="user")
    videos = relationship("Video", back_populates="user")
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"


class Query(Base):
    """Model for user queries."""
    __tablename__ = "queries"
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous queries
    query_type = Column(String(50), nullable=False, index=True)  # video, frame, audio, etc.
    query_data_path = Column(String(512), nullable=True)  # Path to query data
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processing_time = Column(Float, nullable=True)  # Processing time in milliseconds
    status = Column(String(50), default="queued", nullable=False, index=True)  # queued, processing, completed, error
    error_message = Column(Text, nullable=True)  # Error message if status is error
    result_count = Column(Integer, default=0, nullable=False)  # Number of results
    parameters = Column(JSON, nullable=True)  # Query parameters as JSON
    client_info = Column(JSON, nullable=True)  # Client info (device, browser, etc.)
    ip_address = Column(String(50), nullable=True)  # Client IP address
    
    # Relationships
    user = relationship("User", back_populates="queries")
    results = relationship("QueryResult", back_populates="query")
    
    def __repr__(self):
        return f"<Query(id='{self.id}', user_id='{self.user_id}', type='{self.query_type}')>"


class QueryResult(Base):
    """Model for query results."""
    __tablename__ = "query_results"
    
    id = Column(String(36), primary_key=True)  # UUID
    query_id = Column(String(36), ForeignKey("queries.id"), nullable=False, index=True)
    content_id = Column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    segment_id = Column(String(36), ForeignKey("video_segments.id"), nullable=True, index=True)
    confidence = Column(Float, nullable=False, index=True)
    match_type = Column(String(50), nullable=False)  # Type of match (hash, cnn, etc.)
    rank = Column(Integer, nullable=False)  # Rank in the result set
    timestamp = Column(Float, nullable=True)  # Matched timestamp in video
    duration = Column(Float, nullable=True)  # Duration of the matched segment
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    additional_data = Column(JSON, nullable=True)  # Additional result data
    
    # Relationships
    query = relationship("Query", back_populates="results")
    video = relationship("Video", foreign_keys=[content_id])
    segment = relationship("VideoSegment", foreign_keys=[segment_id])
    
    def __repr__(self):
        return f"<QueryResult(id='{self.id}', query_id='{self.query_id}', content_id='{self.content_id}', confidence={self.confidence})>"
