"""Video Processing Module

This module handles video processing tasks such as frame extraction and scene detection.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union, Generator
import cv2
import ffmpeg
import tempfile
import os
from pathlib import Path
from scenedetect import VideoManager, SceneManager, StatsManager
from scenedetect.detectors import ContentDetector
from scenedetect.scene_manager import save_images

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing operations."""
    
    def __init__(self, scene_threshold: float = 30.0, sample_rate: int = 1):
        """Initialize the video processor.
        
        Args:
            scene_threshold: Threshold for scene detection
            sample_rate: Number of frames to sample per second (0 for all frames)
        """
        self.scene_threshold = scene_threshold
        self.sample_rate = sample_rate
    
    def extract_frames(
        self, 
        video_path: str,
        max_frames: int = 100,
        uniform_sampling: bool = True
    ) -> List[np.ndarray]:
        """Extract frames from a video file.
        
        Args:
            video_path: Path to the video file
            max_frames: Maximum number of frames to extract
            uniform_sampling: Whether to sample frames uniformly
            
        Returns:
            List of extracted frames as numpy arrays
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Error opening video file: {video_path}")
        
        try:
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            
            logger.info(f"Video info: {frame_count} frames, {fps:.2f} fps, {duration:.2f} seconds")
            
            frames = []
            
            if uniform_sampling and frame_count > max_frames:
                # Calculate frame indices for uniform sampling
                if self.sample_rate > 0 and (frame_count / fps) > (max_frames / self.sample_rate):
                    # Use the specified sample rate
                    sample_interval = int(fps / self.sample_rate)
                    frame_indices = [i for i in range(0, frame_count, sample_interval)][:max_frames]
                else:
                    # Sample frames uniformly
                    frame_indices = [int(i * frame_count / max_frames) for i in range(max_frames)]
                
                # Extract the selected frames
                for idx in frame_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ret, frame = cap.read()
                    if ret:
                        # Convert BGR to RGB (OpenCV uses BGR by default)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame_rgb)
            else:
                # Extract frames sequentially
                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret or frame_count >= max_frames:
                        break
                    
                    if self.sample_rate > 0:
                        # Sample at the specified rate
                        if frame_count % int(fps / self.sample_rate) == 0:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            frames.append(frame_rgb)
                    else:
                        # Get every frame
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame_rgb)
                    
                    frame_count += 1
            
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            return frames
            
        finally:
            cap.release()
    
    def detect_scenes(
        self, 
        video_path: str,
        output_dir: Optional[str] = None,
        save_keyframes: bool = False
    ) -> List[Tuple[float, float]]:
        """Detect scene changes in a video.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save keyframes (if save_keyframes is True)
            save_keyframes: Whether to save keyframes from each scene
            
        Returns:
            List of scene boundaries as (start_time, end_time) tuples in seconds
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create video manager and scene manager
        video_manager = VideoManager([video_path])
        stats_manager = StatsManager()
        scene_manager = SceneManager(stats_manager)
        
        # Add content detector with threshold
        scene_manager.add_detector(ContentDetector(threshold=self.scene_threshold))
        
        # Start video manager
        video_manager.start()
        
        # Perform scene detection
        scene_manager.detect_scenes(frame_source=video_manager)
        
        # Get the list of detected scenes
        scene_list = scene_manager.get_scene_list()
        
        # Convert scene_list to (start_time, end_time) tuples
        scenes = []
        for scene in scene_list:
            start_time = scene[0].get_seconds()
            end_time = scene[1].get_seconds()
            scenes.append((start_time, end_time))
        
        # Save keyframes if requested
        if save_keyframes and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            save_images(scene_list, video_manager, num_images=1, output_dir=output_dir)
        
        logger.info(f"Detected {len(scenes)} scenes in {video_path}")
        return scenes
    
    def extract_keyframes(
        self, 
        video_path: str,
        max_keyframes: int = 10
    ) -> List[np.ndarray]:
        """Extract keyframes from a video based on scene detection.
        
        Args:
            video_path: Path to the video file
            max_keyframes: Maximum number of keyframes to extract
            
        Returns:
            List of keyframes as numpy arrays
        """
        # Detect scenes
        scenes = self.detect_scenes(video_path)
        
        # Determine which scenes to use for keyframes
        if len(scenes) <= max_keyframes:
            # Use all scenes
            selected_scenes = scenes
        else:
            # Select scenes uniformly
            indices = [int(i * len(scenes) / max_keyframes) for i in range(max_keyframes)]
            selected_scenes = [scenes[i] for i in indices]
        
        # Extract the middle frame from each scene
        keyframes = []
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        try:
            for start_time, end_time in selected_scenes:
                # Calculate the middle frame position
                middle_time = (start_time + end_time) / 2
                frame_pos = int(middle_time * fps)
                
                # Extract the frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    keyframes.append(frame_rgb)
        finally:
            cap.release()
        
        logger.info(f"Extracted {len(keyframes)} keyframes from {video_path}")
        return keyframes
    
    def extract_audio(self, video_path: str) -> Tuple[np.ndarray, int]:
        """Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_audio_path = temp_file.name
        
        try:
            # Extract audio using ffmpeg
            (ffmpeg
             .input(video_path)
             .output(temp_audio_path, acodec='pcm_s16le', ac=1, ar='44100')
             .overwrite_output()
             .run(quiet=True))
            
            # Load the audio file
            import librosa
            audio_data, sample_rate = librosa.load(temp_audio_path, sr=None)
            
            logger.info(f"Extracted audio from {video_path}: {len(audio_data)/sample_rate:.2f} seconds at {sample_rate} Hz")
            return audio_data, sample_rate
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    def create_video_summary(self, video_path: str, output_path: str, duration: int = 10):
        """Create a short summary of a video by extracting key scenes.
        
        Args:
            video_path: Path to the input video
            output_path: Path to save the output summary video
            duration: Target duration of the summary in seconds
        """
        # Detect scenes
        scenes = self.detect_scenes(video_path)
        
        # Get video properties
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Sort scenes by length and select the top N scenes
        scene_durations = [(i, end - start) for i, (start, end) in enumerate(scenes)]
        scene_durations.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate how many scenes to include
        total_video_duration = scenes[-1][1] if scenes else 0
        summary_ratio = min(1.0, duration / total_video_duration)
        
        target_scenes_count = max(1, int(len(scenes) * summary_ratio))
        selected_scene_indices = [x[0] for x in scene_durations[:target_scenes_count]]
        selected_scene_indices.sort()  # Sort by scene order in the original video
        
        # Create temporary directory for scene clips
        with tempfile.TemporaryDirectory() as temp_dir:
            scene_clips = []
            
            # Extract each selected scene
            for i, scene_idx in enumerate(selected_scene_indices):
                start_time, end_time = scenes[scene_idx]
                clip_path = os.path.join(temp_dir, f"scene_{i:03d}.mp4")
                
                # Limit scene duration if needed
                scene_duration = end_time - start_time
                if scene_duration > duration / target_scenes_count:
                    # Trim to keep the middle portion
                    center = (start_time + end_time) / 2
                    half_target = (duration / target_scenes_count) / 2
                    start_time = max(start_time, center - half_target)
                    end_time = min(end_time, center + half_target)
                
                # Extract the scene clip using ffmpeg
                (ffmpeg
                 .input(video_path, ss=start_time, to=end_time)
                 .output(clip_path, c='copy')
                 .overwrite_output()
                 .run(quiet=True))
                
                scene_clips.append(clip_path)
            
            # Create a file with the list of clips
            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, "w") as f:
                for clip_path in scene_clips:
                    f.write(f"file '{clip_path}'\n")
            
            # Concatenate clips to create the summary video
            (ffmpeg
             .input(concat_file, format='concat', safe=0)
             .output(output_path, c='copy')
             .overwrite_output()
             .run(quiet=True))
        
        logger.info(f"Created video summary at {output_path} with {len(selected_scene_indices)} scenes")


class VideoThumbnailGenerator:
    """Generates thumbnails from videos."""
    
    def __init__(self, processor: Optional[VideoProcessor] = None):
        """Initialize the thumbnail generator.
        
        Args:
            processor: Video processor to use for frame extraction
        """
        self.processor = processor or VideoProcessor()
    
    def generate_thumbnail(self, video_path: str, output_path: str, method: str = 'keyframe'):
        """Generate a thumbnail image from a video.
        
        Args:
            video_path: Path to the video file
            output_path: Path to save the thumbnail image
            method: Method to use for thumbnail generation ('keyframe', 'first', 'middle', 'mosaic')
        """
        if method == 'keyframe':
            # Extract the first keyframe
            keyframes = self.processor.extract_keyframes(video_path, max_keyframes=1)
            if keyframes:
                thumbnail = keyframes[0]
                cv2.imwrite(output_path, cv2.cvtColor(thumbnail, cv2.COLOR_RGB2BGR))
                return
        
        elif method == 'first':
            # Extract the first frame
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(output_path, frame)
                return
        
        elif method == 'middle':
            # Extract the middle frame
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(output_path, frame)
                return
        
        elif method == 'mosaic':
            # Create a mosaic of frames
            frames = self.processor.extract_frames(video_path, max_frames=9, uniform_sampling=True)
            if frames:
                # Determine the grid size
                grid_size = int(np.ceil(np.sqrt(len(frames))))
                
                # Resize frames to a smaller size
                thumbnail_size = (180, 180)
                resized_frames = [cv2.resize(frame, thumbnail_size) for frame in frames]
                
                # Create a blank mosaic image
                mosaic = np.zeros((grid_size * thumbnail_size[0], grid_size * thumbnail_size[1], 3), dtype=np.uint8)
                
                # Fill the mosaic with frames
                for i, frame in enumerate(resized_frames):
                    row = i // grid_size
                    col = i % grid_size
                    mosaic[row*thumbnail_size[0]:(row+1)*thumbnail_size[0], 
                            col*thumbnail_size[1]:(col+1)*thumbnail_size[1]] = frame
                
                cv2.imwrite(output_path, cv2.cvtColor(mosaic, cv2.COLOR_RGB2BGR))
                return
        
        # If all methods fail or an invalid method is specified, use a default approach
        logger.warning(f"Failed to generate thumbnail using method '{method}', falling back to default")
        
        # Default: extract a frame from the first second
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(fps), 10))
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            cv2.imwrite(output_path, frame)
        else:
            logger.error(f"Failed to generate thumbnail for {video_path}")
    
    def generate_thumbnail_grid(self, video_path: str, output_path: str, rows: int = 3, cols: int = 3):
        """Generate a grid of thumbnails from a video.
        
        Args:
            video_path: Path to the video file
            output_path: Path to save the thumbnail grid image
            rows: Number of rows in the grid
            cols: Number of columns in the grid
        """
        # Extract uniformly sampled frames
        frames = self.processor.extract_frames(video_path, max_frames=rows*cols, uniform_sampling=True)
        
        if not frames:
            logger.error(f"Failed to extract frames from {video_path}")
            return
        
        # Resize frames
        thumbnail_width = 320
        thumbnail_height = 180
        resized_frames = [cv2.resize(frame, (thumbnail_width, thumbnail_height)) for frame in frames]
        
        # Create the grid image
        grid = np.zeros((rows * thumbnail_height, cols * thumbnail_width, 3), dtype=np.uint8)
        
        # Fill the grid with frames
        for i, frame in enumerate(resized_frames):
            if i >= rows * cols:
                break
                
            row = i // cols
            col = i % cols
            
            grid[row*thumbnail_height:(row+1)*thumbnail_height, 
                 col*thumbnail_width:(col+1)*thumbnail_width] = frame
        
        # Save the grid image
        cv2.imwrite(output_path, cv2.cvtColor(grid, cv2.COLOR_RGB2BGR))
        logger.info(f"Generated thumbnail grid at {output_path}")
