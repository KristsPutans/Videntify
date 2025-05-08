"""Feature Extraction Pipeline Module

This module implements the complete feature extraction pipeline for the VidID system.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import os
import json
from pathlib import Path
from datetime import datetime
import uuid

from .base import FeatureVector, BaseFeatureExtractor, MultiModalFeatureExtractor, FeatureExtractorFactory
from .visual import CNNFeatureExtractor, PerceptualHashExtractor, MotionFeatureExtractor
from .audio import MFCCExtractor, AudioFingerprint, WaveformStatisticsExtractor
from .video_processor import VideoProcessor, VideoThumbnailGenerator

logger = logging.getLogger(__name__)


class FeatureExtractionPipeline:
    """Complete pipeline for extracting features from videos."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        feature_storage: Optional['FeatureStorage'] = None
    ):
        """Initialize the feature extraction pipeline.
        
        Args:
            config: Configuration for the pipeline
            feature_storage: Storage for extracted features
        """
        self.config = config or {}
        self.feature_storage = feature_storage
        
        # Set up GPU usage if available
        gpu_enabled = self.config.get('gpu_enabled', True)
        self.device = 'cuda' if gpu_enabled and self._is_gpu_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        # Set up video processor
        scene_threshold = self.config.get('scene_detection_threshold', 30.0)
        sample_rate = self.config.get('sample_rate', 1)
        self.video_processor = VideoProcessor(scene_threshold=scene_threshold, sample_rate=sample_rate)
        
        # Set up feature extractors
        self._setup_extractors()
    
    def _is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _setup_extractors(self):
        """Set up the feature extractors."""
        # Visual feature extractors
        self.visual_extractors = {
            'cnn': CNNFeatureExtractor(
                model_name=self.config.get('cnn_model', 'resnet50'),
                model_path=self.config.get('cnn_model_path'),
                device=self.device
            ),
            'phash': PerceptualHashExtractor(
                hash_size=self.config.get('phash_size', 16),
                device=self.device
            ),
            'motion': MotionFeatureExtractor(
                window_size=self.config.get('motion_window_size', 5),
                feature_dim=self.config.get('motion_feature_dim', 128),
                device=self.device
            )
        }
        
        # Audio feature extractors
        self.audio_extractors = {
            'mfcc': MFCCExtractor(
                n_mfcc=self.config.get('n_mfcc', 20),
                feature_dim=self.config.get('mfcc_feature_dim', 256),
                device=self.device
            ),
            'audio_fingerprint': AudioFingerprint(
                feature_dim=self.config.get('audio_fingerprint_dim', 512),
                device=self.device
            ),
            'waveform_stats': WaveformStatisticsExtractor(
                feature_dim=self.config.get('waveform_feature_dim', 64),
                device=self.device
            )
        }
        
        # Create multi-modal extractors
        visual_weights = self.config.get('visual_weights', {'cnn': 0.6, 'phash': 0.2, 'motion': 0.2})
        self.visual_multimodal = MultiModalFeatureExtractor(self.visual_extractors, weights=visual_weights)
        
        audio_weights = self.config.get('audio_weights', {
            'mfcc': 0.4, 'audio_fingerprint': 0.4, 'waveform_stats': 0.2
        })
        self.audio_multimodal = MultiModalFeatureExtractor(self.audio_extractors, weights=audio_weights)
        
        # Combined extractor
        self.combined_multimodal = MultiModalFeatureExtractor({
            'visual': self.visual_multimodal,
            'audio': self.audio_multimodal
        }, weights=self.config.get('modality_weights', {'visual': 0.6, 'audio': 0.4}))
    
    def extract_features_from_video(self, video_path: str, video_id: Optional[str] = None) -> Dict[str, FeatureVector]:
        """Extract all features from a video file.
        
        Args:
            video_path: Path to the video file
            video_id: Optional video ID (generated if not provided)
            
        Returns:
            Dictionary of feature vectors by extractor name
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Generate video ID if not provided
        video_id = video_id or str(uuid.uuid4())
        
        logger.info(f"Extracting features from video: {video_path} (ID: {video_id})")
        
        # Extract video frames and keyframes
        batch_size = self.config.get('batch_size', 32)
        max_frames = self.config.get('max_frames', 100)
        frames = self.video_processor.extract_frames(video_path, max_frames=max_frames, uniform_sampling=True)
        keyframes = self.video_processor.extract_keyframes(video_path, max_keyframes=min(10, max_frames//10))
        
        # Extract audio
        try:
            audio_data, sample_rate = self.video_processor.extract_audio(video_path)
            audio_input = {'audio': audio_data, 'sample_rate': sample_rate}
            audio_available = True
        except Exception as e:
            logger.warning(f"Failed to extract audio from {video_path}: {e}")
            audio_input = None
            audio_available = False
        
        # Extract visual features from frames
        visual_features = {}
        for name, extractor in self.visual_extractors.items():
            try:
                if name == 'motion' and len(frames) >= 2:
                    feature_vector = extractor(frames)
                else:
                    feature_vector = extractor(frames or keyframes)
                visual_features[name] = feature_vector
            except Exception as e:
                logger.error(f"Error extracting {name} features: {e}")
        
        # Extract audio features
        audio_features = {}
        if audio_available and audio_input:
            for name, extractor in self.audio_extractors.items():
                try:
                    feature_vector = extractor(audio_input)
                    audio_features[name] = feature_vector
                except Exception as e:
                    logger.error(f"Error extracting {name} features: {e}")
        
        # Extract multimodal features
        all_features = {}
        
        # Add individual features
        for name, feature in visual_features.items():
            all_features[f"visual_{name}"] = feature
        
        for name, feature in audio_features.items():
            all_features[f"audio_{name}"] = feature
        
        # Add combined features
        if visual_features:
            visual_combined = self.visual_multimodal({'visual': frames})
            all_features['visual_combined'] = visual_combined
        
        if audio_features:
            audio_combined = self.audio_multimodal({'audio': audio_input})
            all_features['audio_combined'] = audio_combined
        
        # Add overall combined features if both modalities are available
        if visual_features and audio_features:
            combined_input = {
                'visual': frames,
                'audio': audio_input
            }
            combined = self.combined_multimodal(combined_input)
            all_features['combined'] = combined
        
        # Store features if storage is available
        if self.feature_storage:
            metadata = {
                'video_id': video_id,
                'video_path': video_path,
                'frame_count': len(frames),
                'keyframe_count': len(keyframes),
                'extraction_time': datetime.now().isoformat(),
                'audio_available': audio_available
            }
            self.feature_storage.store_features(video_id, all_features, metadata)
        
        return all_features
    
    def extract_features_from_image(self, image_path: str, image_id: Optional[str] = None) -> Dict[str, FeatureVector]:
        """Extract features from an image file.
        
        Args:
            image_path: Path to the image file
            image_id: Optional image ID (generated if not provided)
            
        Returns:
            Dictionary of feature vectors by extractor name
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Generate image ID if not provided
        image_id = image_id or str(uuid.uuid4())
        
        logger.info(f"Extracting features from image: {image_path} (ID: {image_id})")
        
        # Load the image
        import cv2
        from PIL import Image
        
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Extract visual features
        visual_features = {}
        for name, extractor in self.visual_extractors.items():
            if name != 'motion':  # Skip motion extractor for single images
                try:
                    feature_vector = extractor(image_rgb)
                    visual_features[name] = feature_vector
                except Exception as e:
                    logger.error(f"Error extracting {name} features: {e}")
        
        # Create PIL image for extractors that require it
        pil_image = Image.fromarray(image_rgb)
        for name, extractor in self.visual_extractors.items():
            if name == 'cnn':  # CNN extractor can use PIL image directly
                try:
                    feature_vector = extractor(pil_image)
                    visual_features[f"{name}_pil"] = feature_vector
                except Exception as e:
                    logger.error(f"Error extracting {name} features: {e}")
        
        # Add combined visual features
        visual_combined = self.visual_multimodal({'visual': [image_rgb]})
        visual_features['visual_combined'] = visual_combined
        
        # Store features if storage is available
        if self.feature_storage:
            metadata = {
                'image_id': image_id,
                'image_path': image_path,
                'extraction_time': datetime.now().isoformat()
            }
            self.feature_storage.store_features(image_id, visual_features, metadata, content_type='image')
        
        return visual_features
    
    def compare_features(self, feature1: FeatureVector, feature2: FeatureVector) -> float:
        """Compare two feature vectors and return similarity score.
        
        Args:
            feature1: First feature vector
            feature2: Second feature vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if feature1.dimension != feature2.dimension:
            raise ValueError(f"Feature dimensions don't match: {feature1.dimension} vs {feature2.dimension}")
        
        # Normalize vectors if needed
        vec1 = feature1.vector / np.linalg.norm(feature1.vector) if np.linalg.norm(feature1.vector) > 0 else feature1.vector
        vec2 = feature2.vector / np.linalg.norm(feature2.vector) if np.linalg.norm(feature2.vector) > 0 else feature2.vector
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8)
        
        # Return similarity score between 0 and 1
        return float((similarity + 1) / 2)
    
    def create_thumbnail(self, video_path: str, output_path: str, method: str = 'keyframe'):
        """Generate a thumbnail for a video.
        
        Args:
            video_path: Path to the video file
            output_path: Path to save the thumbnail
            method: Method to use ('keyframe', 'first', 'middle', 'mosaic')
        """
        thumbnail_generator = VideoThumbnailGenerator(self.video_processor)
        thumbnail_generator.generate_thumbnail(video_path, output_path, method)


class FeatureStorage:
    """Base class for feature vector storage."""
    
    def store_features(self, content_id: str, features: Dict[str, FeatureVector], 
                      metadata: Optional[Dict[str, Any]] = None, content_type: str = 'video'):
        """Store feature vectors.
        
        Args:
            content_id: ID of the content
            features: Dictionary of feature vectors by extractor name
            metadata: Optional metadata
            content_type: Type of content ('video' or 'image')
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def retrieve_features(self, content_id: str) -> Dict[str, FeatureVector]:
        """Retrieve feature vectors for a content ID.
        
        Args:
            content_id: ID of the content
            
        Returns:
            Dictionary of feature vectors by extractor name
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def search_similar(self, feature_vector: FeatureVector, feature_type: str, 
                       limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar content.
        
        Args:
            feature_vector: Query feature vector
            feature_type: Type of feature to compare
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching results with similarity scores
        """
        raise NotImplementedError("Subclasses must implement this method")


class FileSystemFeatureStorage(FeatureStorage):
    """Store feature vectors in the file system."""
    
    def __init__(self, storage_dir: str):
        """Initialize the file system feature storage.
        
        Args:
            storage_dir: Directory to store feature vectors
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / 'index.json'
        
        # Load or create index
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {}
    
    def _save_index(self):
        """Save the index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def store_features(self, content_id: str, features: Dict[str, FeatureVector], 
                      metadata: Optional[Dict[str, Any]] = None, content_type: str = 'video'):
        """Store feature vectors in the file system.
        
        Args:
            content_id: ID of the content
            features: Dictionary of feature vectors by extractor name
            metadata: Optional metadata
            content_type: Type of content ('video' or 'image')
        """
        # Create content directory
        content_dir = self.storage_dir / content_id
        content_dir.mkdir(exist_ok=True)
        
        # Store each feature vector
        stored_features = {}
        for name, feature in features.items():
            feature_path = content_dir / f"{name}.json"
            with open(feature_path, 'w') as f:
                json.dump(feature.to_dict(), f, indent=2)
            stored_features[name] = str(feature_path.relative_to(self.storage_dir))
        
        # Update index
        self.index[content_id] = {
            'id': content_id,
            'type': content_type,
            'features': stored_features,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save index
        self._save_index()
        
        logger.info(f"Stored {len(features)} features for {content_type} {content_id}")
    
    def retrieve_features(self, content_id: str) -> Dict[str, FeatureVector]:
        """Retrieve feature vectors from the file system.
        
        Args:
            content_id: ID of the content
            
        Returns:
            Dictionary of feature vectors by extractor name
        """
        if content_id not in self.index:
            raise KeyError(f"Content ID not found: {content_id}")
        
        content_info = self.index[content_id]
        features = {}
        
        for name, relative_path in content_info['features'].items():
            feature_path = self.storage_dir / relative_path
            if feature_path.exists():
                with open(feature_path, 'r') as f:
                    feature_data = json.load(f)
                    features[name] = FeatureVector.from_dict(feature_data)
        
        return features
    
    def search_similar(self, feature_vector: FeatureVector, feature_type: str, 
                       limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar content in the file system.
        
        Args:
            feature_vector: Query feature vector
            feature_type: Type of feature to compare
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching results with similarity scores
        """
        results = []
        
        for content_id, content_info in self.index.items():
            # Skip if feature type is not available
            if feature_type not in content_info['features']:
                continue
            
            # Load the feature vector
            feature_path = self.storage_dir / content_info['features'][feature_type]
            if not feature_path.exists():
                continue
            
            try:
                with open(feature_path, 'r') as f:
                    stored_feature = FeatureVector.from_dict(json.load(f))
                
                # Calculate similarity
                similarity = self._calculate_similarity(feature_vector, stored_feature)
                
                # Add to results if above threshold
                if similarity >= threshold:
                    results.append({
                        'id': content_id,
                        'type': content_info['type'],
                        'similarity': similarity,
                        'metadata': content_info['metadata']
                    })
            except Exception as e:
                logger.error(f"Error comparing with {content_id}: {e}")
        
        # Sort by similarity (descending) and limit results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def _calculate_similarity(self, feature1: FeatureVector, feature2: FeatureVector) -> float:
        """Calculate similarity between two feature vectors.
        
        Args:
            feature1: First feature vector
            feature2: Second feature vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if feature1.dimension != feature2.dimension:
            logger.warning(f"Feature dimensions don't match: {feature1.dimension} vs {feature2.dimension}")
            return 0.0
        
        # Normalize vectors
        vec1 = feature1.vector / np.linalg.norm(feature1.vector) if np.linalg.norm(feature1.vector) > 0 else feature1.vector
        vec2 = feature2.vector / np.linalg.norm(feature2.vector) if np.linalg.norm(feature2.vector) > 0 else feature2.vector
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8)
        
        # Return similarity score between 0 and 1
        return float((similarity + 1) / 2)
