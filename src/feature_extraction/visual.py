"""Visual Feature Extraction Module

This module implements visual feature extraction for the VidID system using deep learning models.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from pathlib import Path

from .base import FeatureVector, VideoFeatureExtractor, FeatureExtractorFactory

logger = logging.getLogger(__name__)

# Define standard image transformations for models
STANDARD_TRANSFORMS = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class CNNFeatureExtractor(VideoFeatureExtractor):
    """Feature extractor using a pre-trained CNN model."""
    
    def __init__(
        self, 
        model_name: str = 'resnet50', 
        layer_name: str = 'avgpool',
        model_path: Optional[str] = None,
        device: str = 'cpu',
        transform: Optional[transforms.Compose] = None
    ):
        """Initialize the CNN feature extractor.
        
        Args:
            model_name: Name of the model architecture ('resnet50', 'densenet121', etc.)
            layer_name: Name of the layer to extract features from
            model_path: Path to a pre-trained model file (if None, use default pre-trained weights)
            device: Device to run the model on ('cpu' or 'cuda')
            transform: Image transformations to apply (if None, use standard transforms)
        """
        super().__init__(model_path=model_path, device=device)
        self.model_name = model_name
        self.layer_name = layer_name
        self.transform = transform or STANDARD_TRANSFORMS
        self.feature_dim = None
        self.features = None
    
    def initialize(self) -> None:
        """Initialize the CNN model."""
        device = torch.device(self.device if torch.cuda.is_available() and self.device == 'cuda' else 'cpu')
        
        # Load the model
        if self.model_name == 'resnet50':
            model = models.resnet50(pretrained=True)
            self.feature_dim = 2048
        elif self.model_name == 'resnet18':
            model = models.resnet18(pretrained=True)
            self.feature_dim = 512
        elif self.model_name == 'densenet121':
            model = models.densenet121(pretrained=True)
            self.feature_dim = 1024
        elif self.model_name == 'vgg16':
            model = models.vgg16(pretrained=True)
            self.feature_dim = 4096
            # For VGG, use the classifier features
            self.layer_name = 'classifier.6'
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
        
        # Load custom weights if provided
        if self.model_path:
            if Path(self.model_path).exists():
                state_dict = torch.load(self.model_path, map_location=device)
                model.load_state_dict(state_dict)
                logger.info(f"Loaded model weights from {self.model_path}")
            else:
                logger.warning(f"Model file not found: {self.model_path}")
        
        # Set up feature extraction hook
        self.features = {}
        
        def get_features(name):
            def hook(model, input, output):
                # Handle different output types
                if isinstance(output, torch.Tensor):
                    self.features[name] = output.detach()
                elif isinstance(output, tuple):
                    self.features[name] = output[0].detach()
            return hook
        
        # Register hook to extract features from the specified layer
        if '.' in self.layer_name:
            # Handle nested attributes like 'classifier.6'
            parts = self.layer_name.split('.')
            layer = model
            for part in parts:
                layer = getattr(layer, part)
            layer.register_forward_hook(get_features(self.layer_name))
        else:
            # Direct attribute like 'avgpool'
            getattr(model, self.layer_name).register_forward_hook(get_features(self.layer_name))
        
        # Move model to device and set to eval mode
        self.model = model.to(device)
        self.model.eval()
        logger.info(f"Initialized {self.model_name} feature extractor on {device}")
    
    def extract_frame(self, frame: np.ndarray) -> np.ndarray:
        """Extract features from a single video frame.
        
        Args:
            frame: Video frame as a numpy array (H, W, C) in RGB format
            
        Returns:
            Frame feature vector
        """
        # Convert numpy array to PIL Image
        image = Image.fromarray(frame)
        return self._extract_image(image)
    
    def _extract_image(self, image: Image.Image) -> np.ndarray:
        """Extract features from a PIL Image.
        
        Args:
            image: PIL Image
            
        Returns:
            Image feature vector
        """
        device = next(self.model.parameters()).device
        
        # Apply transformations and add batch dimension
        input_tensor = self.transform(image).unsqueeze(0).to(device)
        
        # Forward pass
        with torch.no_grad():
            _ = self.model(input_tensor)
        
        # Get features from the registered hook
        features = self.features[self.layer_name]
        
        # Reshape features to a flat vector
        if len(features.shape) == 4:  # For convolutional features
            features = nn.functional.adaptive_avg_pool2d(features, (1, 1))
        features = features.view(features.size(0), -1).cpu().numpy()
        
        return features[0]  # Return the features for the first (only) image
    
    def aggregate_features(self, frame_features: List[np.ndarray]) -> np.ndarray:
        """Aggregate frame features into a video feature.
        
        Args:
            frame_features: List of frame feature vectors
            
        Returns:
            Aggregated video feature vector
        """
        if not frame_features:
            return np.zeros(self.feature_dim)
        
        # Simple mean aggregation (can be extended with more sophisticated methods)
        return np.mean(frame_features, axis=0)
    
    def extract(self, input_data: Union[np.ndarray, List[np.ndarray], Image.Image]) -> FeatureVector:
        """Extract features from the input data.
        
        Args:
            input_data: Input data (single frame, list of frames, or PIL Image)
            
        Returns:
            Extracted feature vector
        """
        if not self._initialized:
            self.initialize()
            self._initialized = True
        
        if isinstance(input_data, Image.Image):
            # Extract features from a single PIL Image
            features = self._extract_image(input_data)
            return FeatureVector(features, {'type': 'image'})
        
        elif isinstance(input_data, np.ndarray) and input_data.ndim == 3:
            # Extract features from a single frame
            features = self.extract_frame(input_data)
            return FeatureVector(features, {'type': 'frame'})
        
        elif isinstance(input_data, list) and all(isinstance(frame, np.ndarray) for frame in input_data):
            # Extract features from multiple frames
            frame_features = [self.extract_frame(frame) for frame in input_data]
            aggregated_features = self.aggregate_features(frame_features)
            return FeatureVector(aggregated_features, {
                'type': 'video',
                'frame_count': len(input_data)
            })
        
        else:
            raise ValueError(f"Unsupported input type for CNNFeatureExtractor: {type(input_data)}")


class PerceptualHashExtractor(VideoFeatureExtractor):
    """Feature extractor using perceptual hashing techniques."""
    
    def __init__(self, hash_size: int = 16, device: str = 'cpu'):
        """Initialize the perceptual hash extractor.
        
        Args:
            hash_size: Size of the hash (hash_size x hash_size)
            device: Device to run the computations on
        """
        super().__init__(device=device)
        self.hash_size = hash_size
        self.feature_dim = hash_size * hash_size
    
    def initialize(self) -> None:
        """Initialize the perceptual hash extractor."""
        # No initialization needed for perceptual hashing
        pass
    
    def extract_frame(self, frame: np.ndarray) -> np.ndarray:
        """Extract perceptual hash from a single video frame.
        
        Args:
            frame: Video frame as a numpy array (H, W, C)
            
        Returns:
            Frame hash as a flattened numpy array
        """
        # Convert to PIL Image
        image = Image.fromarray(frame)
        
        # Resize the image to (hash_size + 1, hash_size)
        image = image.convert('L').resize((self.hash_size + 1, self.hash_size), Image.LANCZOS)
        
        # Compute difference hash (dHash)
        pixels = np.array(image)
        diff = pixels[:, 1:] > pixels[:, :-1]  # Compare adjacent pixels
        
        # Convert boolean array to float for feature vector
        return diff.flatten().astype(np.float32)
    
    def aggregate_features(self, frame_features: List[np.ndarray]) -> np.ndarray:
        """Aggregate frame hashes into a video hash.
        
        Args:
            frame_features: List of frame hash vectors
            
        Returns:
            Aggregated video hash vector
        """
        if not frame_features:
            return np.zeros(self.feature_dim)
        
        # For perceptual hashes, we use majority voting for each bit
        stacked = np.stack(frame_features)
        return (np.mean(stacked, axis=0) > 0.5).astype(np.float32)
    
    def extract(self, input_data: Union[np.ndarray, List[np.ndarray], Image.Image]) -> FeatureVector:
        """Extract perceptual hash from the input data.
        
        Args:
            input_data: Input data (single frame, list of frames, or PIL Image)
            
        Returns:
            Extracted feature vector
        """
        if isinstance(input_data, Image.Image):
            # Convert PIL Image to numpy array
            input_data = np.array(input_data)
        
        if isinstance(input_data, np.ndarray) and input_data.ndim == 3:
            # Extract hash from a single frame
            features = self.extract_frame(input_data)
            return FeatureVector(features, {'type': 'frame_hash'})
        
        elif isinstance(input_data, list) and all(isinstance(frame, np.ndarray) for frame in input_data):
            # Extract hash from multiple frames
            frame_features = [self.extract_frame(frame) for frame in input_data]
            aggregated_features = self.aggregate_features(frame_features)
            return FeatureVector(aggregated_features, {
                'type': 'video_hash',
                'frame_count': len(input_data)
            })
        
        else:
            raise ValueError(f"Unsupported input type for PerceptualHashExtractor: {type(input_data)}")


class MotionFeatureExtractor(VideoFeatureExtractor):
    """Feature extractor for motion patterns in videos."""
    
    def __init__(self, window_size: int = 5, feature_dim: int = 128, device: str = 'cpu'):
        """Initialize the motion feature extractor.
        
        Args:
            window_size: Number of frames to consider for motion analysis
            feature_dim: Dimension of the output feature vector
            device: Device to run the computations on
        """
        super().__init__(device=device)
        self.window_size = window_size
        self.feature_dim = feature_dim
    
    def initialize(self) -> None:
        """Initialize the motion feature extractor."""
        # No initialization needed
        pass
    
    def extract_frame(self, frame: np.ndarray) -> np.ndarray:
        """This method is not applicable for motion features."""
        raise NotImplementedError("Motion features cannot be extracted from a single frame")
    
    def compute_flow(self, frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
        """Compute optical flow between two frames.
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            Optical flow features
        """
        # Convert to grayscale
        if frame1.ndim == 3:
            gray1 = np.mean(frame1, axis=2).astype(np.uint8)
        else:
            gray1 = frame1.astype(np.uint8)
            
        if frame2.ndim == 3:
            gray2 = np.mean(frame2, axis=2).astype(np.uint8)
        else:
            gray2 = frame2.astype(np.uint8)
        
        # Simple frame difference as a basic motion feature
        diff = np.abs(gray2.astype(np.float32) - gray1.astype(np.float32))
        
        # Resize to lower resolution for feature extraction
        h, w = diff.shape
        block_size = min(h, w) // 16
        if block_size < 1:
            block_size = 1
        
        # Compute block-wise motion statistics
        features = []
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                block = diff[i:i+block_size, j:j+block_size]
                if block.size > 0:
                    features.append(np.mean(block))
                    features.append(np.std(block))
        
        # Ensure fixed feature dimension
        if len(features) > self.feature_dim:
            features = features[:self.feature_dim]
        elif len(features) < self.feature_dim:
            features.extend([0] * (self.feature_dim - len(features)))
        
        return np.array(features)
    
    def aggregate_features(self, frame_features: List[np.ndarray]) -> np.ndarray:
        """Aggregate motion features.
        
        Args:
            frame_features: List of motion feature vectors
            
        Returns:
            Aggregated motion feature vector
        """
        if not frame_features:
            return np.zeros(self.feature_dim)
        
        # For motion features, we use mean and standard deviation
        mean_features = np.mean(frame_features, axis=0)
        std_features = np.std(frame_features, axis=0)
        
        # Combine mean and std features
        combined = np.concatenate([mean_features, std_features])
        
        # Ensure fixed feature dimension
        if len(combined) > self.feature_dim:
            combined = combined[:self.feature_dim]
        elif len(combined) < self.feature_dim:
            combined = np.pad(combined, (0, self.feature_dim - len(combined)))
        
        return combined
    
    def extract(self, input_data: List[np.ndarray]) -> FeatureVector:
        """Extract motion features from a sequence of frames.
        
        Args:
            input_data: List of video frames
            
        Returns:
            Motion feature vector
        """
        if not isinstance(input_data, list) or not all(isinstance(frame, np.ndarray) for frame in input_data):
            raise ValueError("Motion feature extraction requires a list of frames")
        
        if len(input_data) < 2:
            return FeatureVector(np.zeros(self.feature_dim), {'type': 'motion', 'frame_count': len(input_data)})
        
        # Compute optical flow between consecutive frames
        flow_features = []
        for i in range(len(input_data) - 1):
            flow = self.compute_flow(input_data[i], input_data[i + 1])
            flow_features.append(flow)
        
        # Aggregate flow features
        aggregated_features = self.aggregate_features(flow_features)
        
        return FeatureVector(aggregated_features, {
            'type': 'motion',
            'frame_count': len(input_data),
            'flow_count': len(flow_features)
        })


# Register feature extractors
FeatureExtractorFactory.register('cnn', CNNFeatureExtractor)
FeatureExtractorFactory.register('phash', PerceptualHashExtractor)
FeatureExtractorFactory.register('motion', MotionFeatureExtractor)
