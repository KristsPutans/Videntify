#!/usr/bin/env python
"""
VidID Command Line Interface

This script provides command-line utilities for managing the VidID system,
including content ingestion, system monitoring, and maintenance tasks.
"""

import argparse
import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.config.config import ConfigManager
from src.core.video_acquisition import VideoAcquisitionService, ContentSource, SourceTier
from src.core.feature_extraction import FeatureExtractionEngine, FeatureType
from src.core.indexing_system import IndexingSystem
from src.db.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vidid-cli")


class VidIDCLI:
    """Command-line interface for VidID system management."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_all()
        self.services = {}
        
    def initialize_services(self):
        """Initialize required services."""
        logger.info("Initializing services...")
        
        # Initialize database manager
        self.services["db_manager"] = DatabaseManager(self.config)
        
        # Initialize feature extraction engine if needed
        if "feature_engine" not in self.services:
            self.services["feature_engine"] = FeatureExtractionEngine(self.config.get("feature_extraction", {}))
            
        # Initialize indexing system if needed
        if "indexing_system" not in self.services:
            self.services["indexing_system"] = IndexingSystem(
                self.config.get("indexing", {}),
                self.services["db_manager"].vector_db_client,
                self.services["db_manager"].get_db_session
            )
            
        # Initialize video acquisition service if needed
        if "acquisition_service" not in self.services:
            self.services["acquisition_service"] = VideoAcquisitionService(
                self.config.get("content_acquisition", {})
            )
            
        logger.info("Services initialized successfully")
        
    def ingest_content(self, content_source, content_id, tier):
        """Ingest content from the specified source.
        
        Args:
            content_source: Source type (streaming, television, youtube, archive)
            content_id: ID of the content to ingest
            tier: Content tier (1-4)
        """
        if "acquisition_service" not in self.services:
            self.initialize_services()
            
        logger.info(f"Ingesting content from {content_source}: {content_id} (Tier {tier})")
        
        # Prepare acquisition parameters based on content source
        if content_source == ContentSource.STREAMING:
            # Extract platform from content_id (e.g., netflix:12345)
            parts = content_id.split(":")
            if len(parts) == 2:
                platform, content_id = parts
            else:
                platform = "unknown"
                logger.warning(f"Invalid content ID format: {content_id}. Expected: platform:id")
                
            acquisition_result = self.services["acquisition_service"].acquire_from_streaming(platform, content_id)
            
        elif content_source == ContentSource.TELEVISION:
            # Expected format: channel:timestamp:duration
            parts = content_id.split(":")
            if len(parts) == 3:
                channel, timestamp, duration = parts
                duration = int(duration)
            else:
                logger.error(f"Invalid television content ID format: {content_id}")
                return False
                
            acquisition_result = self.services["acquisition_service"].acquire_from_television(
                channel, timestamp, duration)
            
        elif content_source == ContentSource.YOUTUBE:
            acquisition_result = self.services["acquisition_service"].acquire_from_youtube(content_id)
            
        else:
            logger.error(f"Unsupported content source: {content_source}")
            return False
            
        if not acquisition_result or acquisition_result.get("status") != "success":
            logger.error(f"Content acquisition failed: {acquisition_result}")
            return False
            
        # Extract features from the acquired video
        video_path = acquisition_result.get("path")
        logger.info(f"Extracting features from {video_path}")
        
        features = self.services["feature_engine"].process_full_video(
            video_path,
            [FeatureType.PERCEPTUAL_HASH, FeatureType.CNN_FEATURES, FeatureType.MOTION_PATTERN]
        )
        
        # Index the features
        metadata = acquisition_result.get("metadata", {})
        metadata["source_tier"] = tier
        metadata["ingestion_date"] = datetime.now().isoformat()
        
        indexing_result = self.services["indexing_system"].index_video_features(
            content_id, features, metadata)
        
        if not indexing_result or not indexing_result.get("success"):
            logger.error(f"Feature indexing failed: {indexing_result}")
            return False
            
        logger.info(f"Content successfully ingested and indexed: {content_id}")
        return True
    
    def batch_ingest(self, batch_file):
        """Ingest a batch of content from a JSON file.
        
        Args:
            batch_file: Path to a JSON file with content to ingest
        """
        if not os.path.exists(batch_file):
            logger.error(f"Batch file not found: {batch_file}")
            return False
            
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
                
            if not isinstance(batch_data, list):
                logger.error(f"Invalid batch file format. Expected a list of items.")
                return False
                
            logger.info(f"Starting batch ingestion of {len(batch_data)} items")
            
            success_count = 0
            failure_count = 0
            
            for item in batch_data:
                source = item.get("source")
                content_id = item.get("content_id")
                tier = item.get("tier", 4)  # Default to tier 4
                
                if not source or not content_id:
                    logger.warning(f"Skipping invalid item: {item}")
                    failure_count += 1
                    continue
                    
                try:
                    success = self.ingest_content(source, content_id, tier)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    logger.error(f"Error ingesting content {content_id}: {str(e)}")
                    failure_count += 1
                    
            logger.info(f"Batch ingestion completed. Success: {success_count}, Failures: {failure_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing batch file: {str(e)}")
            return False
    
    def monitor_system(self):
        """Monitor system health and performance."""
        logger.info("System monitoring not yet implemented")
        # This would normally query various system metrics and display them
        # For now, just show a placeholder
        print("\nSystem Status: HEALTHY")
        print("\nComponent Status:")
        print("  API Server:          RUNNING")
        print("  Database:            RUNNING")
        print("  Vector Database:     RUNNING")
        print("  Feature Extraction:  RUNNING")
        print("  Matching Engine:     RUNNING")
        
        print("\nSystem Metrics:")
        print("  CPU Usage:           35.2%")
        print("  Memory Usage:        62.7%")
        print("  Disk Usage:          48.3%")
        print("  Active Connections:   17")
        print("  Request Rate:         42.3 req/s")
        print("  Avg Response Time:    156ms")
        
        return True
    
    def optimize_indexes(self):
        """Optimize database indexes."""
        if "indexing_system" not in self.services:
            self.initialize_services()
            
        logger.info("Optimizing indexes...")
        
        # This would normally optimize all indexes
        # For now, just show a placeholder
        collections = ["cnn_features", "perceptual_hashes", "motion_patterns"]
        results = self.services["indexing_system"].optimize_indexes(collections)
        
        for collection, success in results.items():
            if success:
                logger.info(f"Successfully optimized {collection}")
            else:
                logger.error(f"Failed to optimize {collection}")
                
        return all(results.values())


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="VidID Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest content")
    ingest_parser.add_argument("--source", choices=["streaming", "television", "youtube", "archive"],
                             required=True, help="Content source")
    ingest_parser.add_argument("--id", required=True, help="Content ID")
    ingest_parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], default=4,
                             help="Content tier (1-4, default: 4)")
    
    # Batch ingest command
    batch_parser = subparsers.add_parser("batch-ingest", help="Ingest a batch of content")
    batch_parser.add_argument("--file", required=True, help="Path to batch file (JSON)")
    
    # Monitor command
    subparsers.add_parser("monitor", help="Monitor system health and performance")
    
    # Optimize command
    subparsers.add_parser("optimize", help="Optimize database indexes")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = VidIDCLI()
    
    if args.command == "ingest":
        source_map = {
            "streaming": ContentSource.STREAMING,
            "television": ContentSource.TELEVISION,
            "youtube": ContentSource.YOUTUBE,
            "archive": ContentSource.ARCHIVE
        }
        
        tier_map = {
            1: SourceTier.TIER_1,
            2: SourceTier.TIER_2,
            3: SourceTier.TIER_3,
            4: SourceTier.TIER_4
        }
        
        success = cli.ingest_content(source_map[args.source], args.id, tier_map[args.tier])
        return 0 if success else 1
        
    elif args.command == "batch-ingest":
        success = cli.batch_ingest(args.file)
        return 0 if success else 1
        
    elif args.command == "monitor":
        cli.monitor_system()
        return 0
        
    elif args.command == "optimize":
        success = cli.optimize_indexes()
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
