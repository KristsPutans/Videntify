"""VidID Feature Extraction Package

This package implements feature extraction capabilities for the VidID video identification system.
"""

from .base import (
    FeatureVector,
    BaseFeatureExtractor,
    VideoFeatureExtractor,
    AudioFeatureExtractor,
    MultiModalFeatureExtractor,
    FeatureExtractorFactory
)

from .visual import (
    CNNFeatureExtractor,
    PerceptualHashExtractor,
    MotionFeatureExtractor
)

from .audio import (
    MFCCExtractor,
    AudioFingerprint,
    WaveformStatisticsExtractor
)

from .video_processor import VideoProcessor, VideoThumbnailGenerator

from .pipeline import (
    FeatureExtractionPipeline,
    FeatureStorage,
    FileSystemFeatureStorage
)

__all__ = [
    # Base classes
    'FeatureVector',
    'BaseFeatureExtractor',
    'VideoFeatureExtractor',
    'AudioFeatureExtractor',
    'MultiModalFeatureExtractor',
    'FeatureExtractorFactory',
    
    # Visual extractors
    'CNNFeatureExtractor',
    'PerceptualHashExtractor',
    'MotionFeatureExtractor',
    
    # Audio extractors
    'MFCCExtractor',
    'AudioFingerprint',
    'WaveformStatisticsExtractor',
    
    # Video processing
    'VideoProcessor',
    'VideoThumbnailGenerator',
    
    # Pipeline
    'FeatureExtractionPipeline',
    'FeatureStorage',
    'FileSystemFeatureStorage'
]
