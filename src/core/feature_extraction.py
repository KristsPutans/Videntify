"""Feature Extraction Engine

This module handles the extraction of features from videos for fingerprinting,
including scene detection, perceptual hashing, and deep learning features.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Any

import cv2
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from scenedetect import ContentDetector, SceneManager, VideoManager
from PIL import Image

logger = logging.getLogger(__name__)


class FeatureType(str, Enum):
    """Types of features that can be extracted from videos."""
    PERCEPTUAL_HASH = "perceptual_hash"
    CNN_FEATURES = "cnn_features"
    SCENE_TRANSITION = "scene_transition"
    MOTION_PATTERN = "motion_pattern"
    AUDIO_SPECTROGRAM = "audio_spectrogram"
    AUDIO_TRANSCRIPT = "audio_transcript"


class FeatureExtractionEngine:
    """Engine for extracting various features from videos."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the feature extraction engine.
        
        Args:
            config: Configuration dictionary for the engine
        """
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.initialize_models()
        logger.info(f"Initialized FeatureExtractionEngine using {self.device}")
    
    def initialize_models(self):
        """Initialize neural network models for feature extraction."""
        # Load pretrained CNN model for feature extraction
        self.cnn_model = models.resnet50(pretrained=True).to(self.device)
        self.cnn_model.eval()
        # Remove the final classification layer to get features
        self.cnn_model = torch.nn.Sequential(*list(self.cnn_model.children())[:-1])
        
        # Define image transforms
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        # Additional models would be initialized here based on the config
        # This is a placeholder for more advanced models like action recognition, etc.
    
    def detect_scenes(self, video_path: str, threshold: float = 30.0) -> List[Tuple[float, float]]:
        """Detect scene transitions in a video.
        
        Args:
            video_path: Path to the video file
            threshold: Threshold for scene detection sensitivity
            
        Returns:
            List of (start_time, end_time) tuples for each detected scene
        """
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        
        # Start video manager and perform scene detection
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        
        # Get scene list and convert to time ranges
        scene_list = scene_manager.get_scene_list()
        fps = video_manager.get_framerate()
        
        # Convert frame numbers to timestamps
        scenes = []
        for scene in scene_list:
            start_time = scene[0].get_seconds()
            end_time = scene[1].get_seconds()
            scenes.append((start_time, end_time))
        
        return scenes
    
    def compute_perceptual_hash(self, frame: np.ndarray) -> str:
        """Compute a perceptual hash for an image frame.
        
        Args:
            frame: Image frame as numpy array
            
        Returns:
            Perceptual hash as a string
        """
        # Convert to grayscale and resize to 8x8
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (8, 8))
        
        # Compute DCT and extract 64 bits
        dct = cv2.dct(np.float32(resized))
        dct_low = dct[:8, :8]
        
        # Compute the average value and generate hash
        avg = np.mean(dct_low)
        hash_bits = (dct_low > avg).flatten()
        
        # Convert boolean array to hash string
        hash_str = ''.join(['1' if b else '0' for b in hash_bits])
        return hash_str
    
    @torch.no_grad()
    def extract_cnn_features(self, frame: np.ndarray) -> np.ndarray:
        """Extract CNN features from an image frame using a pretrained model.
        
        Args:
            frame: Image frame as numpy array
            
        Returns:
            Feature vector as numpy array
        """
        # Convert from numpy to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Preprocess the image
        input_tensor = self.preprocess(pil_image).unsqueeze(0).to(self.device)
        
        # Extract features
        features = self.cnn_model(input_tensor)
        
        # Convert to numpy and flatten
        features_np = features.squeeze().cpu().numpy()
        return features_np
    
    def extract_motion_patterns(self, frames: List[np.ndarray]) -> np.ndarray:
        """Extract motion patterns from a sequence of frames.
        
        Args:
            frames: List of consecutive frames
            
        Returns:
            Motion pattern features
        """
        if len(frames) < 2:
            raise ValueError("At least two frames are required for motion analysis")
        
        # Calculate optical flow between consecutive frames
        flows = []
        for i in range(len(frames) - 1):
            prev_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            next_gray = cv2.cvtColor(frames[i+1], cv2.COLOR_BGR2GRAY)
            
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, next_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            
            # Compute magnitude and angle of flow
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            # Create histogram of flow magnitudes and angles
            mag_hist = np.histogram(mag, bins=10, range=(0, np.max(mag)))[0]
            ang_hist = np.histogram(ang, bins=8, range=(0, 2*np.pi))[0]
            
            # Normalize histograms
            mag_hist = mag_hist / np.sum(mag_hist) if np.sum(mag_hist) > 0 else mag_hist
            ang_hist = ang_hist / np.sum(ang_hist) if np.sum(ang_hist) > 0 else ang_hist
            
            flows.append(np.concatenate([mag_hist, ang_hist]))
        
        # Combine flow features from all frame pairs
        return np.mean(np.array(flows), axis=0)
    
    def process_video_segment(self, 
                           video_path: str, 
                           start_time: float, 
                           end_time: float, 
                           feature_types: List[FeatureType]) -> Dict[str, Any]:
        """Process a video segment and extract specified features.
        
        Args:
            video_path: Path to the video file
            start_time: Start time of the segment in seconds
            end_time: End time of the segment in seconds
            feature_types: List of feature types to extract
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Convert times to frame numbers
        start_frame = int(start_time * fps)
        end_frame = min(int(end_time * fps), frame_count - 1)
        
        # Set video position to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Collect frames for processing
        frames = []
        frame_hashes = []
        cnn_features_list = []
        
        for frame_idx in range(start_frame, end_frame + 1, max(1, int((end_frame - start_frame) / 10))):
            ret, frame = cap.read()
            if not ret:
                break
                
            frames.append(frame)
            
            # Extract perceptual hash if needed
            if FeatureType.PERCEPTUAL_HASH in feature_types:
                frame_hashes.append(self.compute_perceptual_hash(frame))
                
            # Extract CNN features if needed
            if FeatureType.CNN_FEATURES in feature_types:
                cnn_features_list.append(self.extract_cnn_features(frame))
        
        # Release the video capture object
        cap.release()
        
        # Compile features based on requested types
        if FeatureType.PERCEPTUAL_HASH in feature_types:
            features[FeatureType.PERCEPTUAL_HASH] = frame_hashes
            
        if FeatureType.CNN_FEATURES in feature_types:
            features[FeatureType.CNN_FEATURES] = np.mean(np.array(cnn_features_list), axis=0) if cnn_features_list else np.array([])
            
        if FeatureType.MOTION_PATTERN in feature_types and len(frames) >= 2:
            features[FeatureType.MOTION_PATTERN] = self.extract_motion_patterns(frames)
            
        if FeatureType.SCENE_TRANSITION in feature_types:
            # For scene transitions in the segment, we would need a more sophisticated approach
            # This is a simplification
            features[FeatureType.SCENE_TRANSITION] = "Placeholder for scene transition features"
            
        return features
    
    def process_full_video(self, video_path: str, feature_types: List[FeatureType]) -> Dict[str, Any]:
        """Process a full video and extract specified features.
        
        Args:
            video_path: Path to the video file
            feature_types: List of feature types to extract
            
        Returns:
            Dictionary with extracted features and associated metadata
        """
        # First detect scenes in the video
        scenes = self.detect_scenes(video_path)
        
        # Extract features for each scene
        scene_features = []
        for start_time, end_time in scenes:
            features = self.process_video_segment(
                video_path, start_time, end_time, feature_types)
            scene_features.append({
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "features": features
            })
        
        # Get video metadata
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        # Compile the final result
        return {
            "video_path": video_path,
            "metadata": {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration": duration,
                "scene_count": len(scenes)
            },
            "scenes": scene_features
        }
