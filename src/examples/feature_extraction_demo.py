"""Feature Extraction Demo

This script demonstrates how to use the feature extraction pipeline for video identification.
"""

import logging
import os
import sys
from pathlib import Path
import argparse
import json

# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.feature_extraction import (
    FeatureExtractionPipeline,
    FileSystemFeatureStorage,
    CNNFeatureExtractor,
    PerceptualHashExtractor,
    VideoProcessor
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def extract_features(video_path, output_dir, config=None):
    """Extract features from a video file and save them to disk.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save extracted features
        config: Optional configuration dictionary
    """
    # Set up feature storage
    storage = FileSystemFeatureStorage(output_dir)
    
    # Set up the feature extraction pipeline
    pipeline = FeatureExtractionPipeline(config=config, feature_storage=storage)
    
    # Extract features
    features = pipeline.extract_features_from_video(video_path)
    
    # Generate a thumbnail
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    thumbnail_path = os.path.join(output_dir, f"{video_name}_thumbnail.jpg")
    pipeline.create_thumbnail(video_path, thumbnail_path, method='mosaic')
    
    logger.info(f"Extraction complete. Features saved to {output_dir}")
    logger.info(f"Thumbnail saved to {thumbnail_path}")
    
    return features


def compare_videos(video1_path, video2_path, config=None):
    """Compare two videos and calculate similarity scores.
    
    Args:
        video1_path: Path to the first video
        video2_path: Path to the second video
        config: Optional configuration dictionary
    """
    # Set up the feature extraction pipeline (without storage)
    pipeline = FeatureExtractionPipeline(config=config)
    
    # Extract features from both videos
    features1 = pipeline.extract_features_from_video(video1_path)
    features2 = pipeline.extract_features_from_video(video2_path)
    
    # Compare features
    results = {}
    for feature_name in features1.keys():
        if feature_name in features2:
            similarity = pipeline.compare_features(
                features1[feature_name], 
                features2[feature_name]
            )
            results[feature_name] = similarity
    
    # Print results
    logger.info("Similarity scores:")
    for feature_name, similarity in results.items():
        logger.info(f"  {feature_name}: {similarity:.4f}")
    
    # Calculate average similarity
    avg_similarity = sum(results.values()) / len(results) if results else 0
    logger.info(f"Average similarity: {avg_similarity:.4f}")
    
    # Determine if videos are likely the same content
    threshold = 0.85  # Adjust as needed
    if avg_similarity > threshold:
        logger.info("These videos likely contain the same content.")
    else:
        logger.info("These videos appear to be different.")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="VidID Feature Extraction Demo")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract features from a video")
    extract_parser.add_argument("video_path", help="Path to the video file")
    extract_parser.add_argument("--output-dir", "-o", default="features",
                              help="Directory to save extracted features")
    extract_parser.add_argument("--config", "-c", help="Path to config JSON file")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two videos")
    compare_parser.add_argument("video1", help="Path to the first video")
    compare_parser.add_argument("video2", help="Path to the second video")
    compare_parser.add_argument("--config", "-c", help="Path to config JSON file")
    
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if hasattr(args, "config") and args.config:
        with open(args.config, "r") as f:
            config = json.load(f)
    
    if args.command == "extract":
        extract_features(args.video_path, args.output_dir, config)
    elif args.command == "compare":
        compare_videos(args.video1, args.video2, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
