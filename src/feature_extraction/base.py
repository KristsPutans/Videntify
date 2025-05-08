"""Base Feature Extractor Module

This module defines the base interfaces for feature extraction in the VidID system.
"""

import abc
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
import torch
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureVector:
    """Represents a feature vector with metadata."""
    
    def __init__(self, vector: np.ndarray, metadata: Optional[Dict[str, Any]] = None):
        """Initialize a feature vector.
        
        Args:
            vector: The feature vector as a numpy array
            metadata: Optional metadata about the feature vector
        """
        self.vector = vector
        self.metadata = metadata or {}
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the feature vector."""
        return self.vector.shape[0]
    
    def normalize(self) -> 'FeatureVector':
        """Normalize the feature vector to unit length."""
        norm = np.linalg.norm(self.vector)
        if norm > 0:
            normalized_vector = self.vector / norm
        else:
            normalized_vector = self.vector
        return FeatureVector(normalized_vector, self.metadata.copy())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the feature vector to a dictionary."""
        return {
            'vector': self.vector.tolist(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureVector':
        """Create a feature vector from a dictionary."""
        return cls(
            vector=np.array(data['vector']),
            metadata=data.get('metadata', {})
        )


class BaseFeatureExtractor(abc.ABC):
    """Base class for all feature extractors."""
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu'):
        """Initialize the feature extractor.
        
        Args:
            model_path: Path to the model file
            device: Device to run the model on ('cpu' or 'cuda')
        """
        self.model_path = model_path
        self.device = device
        self.model = None
        self._initialized = False
    
    @abc.abstractmethod
    def initialize(self) -> None:
        """Initialize the feature extractor model."""
        pass
    
    @abc.abstractmethod
    def extract(self, input_data: Any) -> FeatureVector:
        """Extract features from the input data.
        
        Args:
            input_data: Input data to extract features from
            
        Returns:
            Extracted feature vector
        """
        pass
    
    def extract_batch(self, batch_data: List[Any]) -> List[FeatureVector]:
        """Extract features from a batch of input data.
        
        Args:
            batch_data: List of input data to extract features from
            
        Returns:
            List of extracted feature vectors
        """
        return [self.extract(data) for data in batch_data]
    
    def __call__(self, input_data: Any) -> FeatureVector:
        """Call the feature extractor on input data.
        
        Args:
            input_data: Input data to extract features from
            
        Returns:
            Extracted feature vector
        """
        if not self._initialized:
            self.initialize()
            self._initialized = True
        return self.extract(input_data)


class VideoFeatureExtractor(BaseFeatureExtractor):
    """Base class for video feature extractors."""
    
    @abc.abstractmethod
    def extract_frame(self, frame: np.ndarray) -> np.ndarray:
        """Extract features from a single video frame.
        
        Args:
            frame: Video frame as a numpy array (H, W, C)
            
        Returns:
            Frame feature vector
        """
        pass
    
    @abc.abstractmethod
    def aggregate_features(self, frame_features: List[np.ndarray]) -> np.ndarray:
        """Aggregate frame features into a video feature.
        
        Args:
            frame_features: List of frame feature vectors
            
        Returns:
            Aggregated video feature vector
        """
        pass


class AudioFeatureExtractor(BaseFeatureExtractor):
    """Base class for audio feature extractors."""
    
    @abc.abstractmethod
    def extract_segment(self, audio_segment: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract features from an audio segment.
        
        Args:
            audio_segment: Audio segment as a numpy array
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Audio feature vector
        """
        pass


class MultiModalFeatureExtractor(BaseFeatureExtractor):
    """Feature extractor that combines multiple modalities."""
    
    def __init__(self, extractors: Dict[str, BaseFeatureExtractor], weights: Optional[Dict[str, float]] = None):
        """Initialize the multi-modal feature extractor.
        
        Args:
            extractors: Dictionary of feature extractors by modality
            weights: Optional dictionary of weights by modality
        """
        super().__init__()
        self.extractors = extractors
        self.weights = weights or {k: 1.0 for k in extractors.keys()}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all feature extractors."""
        for extractor in self.extractors.values():
            if not extractor._initialized:
                extractor.initialize()
        self._initialized = True
    
    def extract(self, input_data: Dict[str, Any]) -> FeatureVector:
        """Extract features from multi-modal input data.
        
        Args:
            input_data: Dictionary of input data by modality
            
        Returns:
            Combined feature vector
        """
        if not self._initialized:
            self.initialize()
        
        features = {}
        metadata = {}
        
        for modality, extractor in self.extractors.items():
            if modality in input_data:
                feature_vector = extractor(input_data[modality])
                features[modality] = feature_vector.vector
                metadata[modality] = feature_vector.metadata
        
        # Combine features (simple weighted average for now)
        combined_vector = None
        total_weight = 0.0
        
        for modality, vector in features.items():
            weight = self.weights.get(modality, 1.0)
            if combined_vector is None:
                combined_vector = weight * vector
            else:
                # Ensure vectors are the same dimension for combining
                if vector.shape[0] != combined_vector.shape[0]:
                    logger.warning(f"Dimension mismatch: {modality} ({vector.shape[0]}) vs combined ({combined_vector.shape[0]})")
                    continue
                combined_vector += weight * vector
            total_weight += weight
        
        if combined_vector is not None and total_weight > 0:
            combined_vector /= total_weight
        
        return FeatureVector(combined_vector, {'modalities': list(features.keys()), 'metadata': metadata})


class FeatureExtractorFactory:
    """Factory for creating feature extractors."""
    
    _extractors = {}
    
    @classmethod
    def register(cls, name: str, extractor_class):
        """Register a feature extractor class.
        
        Args:
            name: Name of the feature extractor
            extractor_class: Feature extractor class
        """
        cls._extractors[name] = extractor_class
    
    @classmethod
    def create(cls, name: str, **kwargs) -> BaseFeatureExtractor:
        """Create a feature extractor by name.
        
        Args:
            name: Name of the feature extractor
            **kwargs: Arguments to pass to the feature extractor constructor
            
        Returns:
            Feature extractor instance
        """
        if name not in cls._extractors:
            raise ValueError(f"Unknown feature extractor: {name}")
        return cls._extractors[name](**kwargs)
