"""Query Processing Engine

This module handles the end-to-end processing of video identification queries.
"""

import logging
import os
import uuid
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import asyncio
import time

import cv2
import numpy as np

from src.core.feature_extraction import FeatureExtractionEngine, FeatureType
from src.core.matching_engine import MatchingEngine, MatchResult, MatchingAlgorithm
from src.core.vector_query_engine import VectorQueryEngine
from src.core.metadata_enrichment import MetadataEnrichmentEngine, EnrichmentPriority

logger = logging.getLogger(__name__)


class QueryProcessingEngine:
    """Engine for processing video identification queries."""
    
    def __init__(self, config: Dict[str, Any], feature_engine: FeatureExtractionEngine, matching_engine: MatchingEngine):
        """Initialize the query processing engine.
        
        Args:
            config: Configuration dictionary
            feature_engine: Feature extraction engine
            matching_engine: Matching engine
        """
        self.config = config
        self.feature_engine = feature_engine
        self.matching_engine = matching_engine
        
        # Initialize vector query engine for fast retrieval
        self.vector_query_engine = VectorQueryEngine(config.get("vector_query", {}))
        
        # Performance and resource settings
        self.temp_dir = config.get("temp_dir", "/tmp")
        self.gpu_enabled = config.get("gpu_enabled", False)
        self.batch_size = config.get("batch_size", 32)
        self.use_temporal_alignment = config.get("use_temporal_alignment", True)
        self.alignment_window = config.get("alignment_window", 5)  # seconds
        
        # Query optimization parameters
        self.prefetch_candidates = config.get("prefetch_candidates", 100)
        self.max_scenes_per_query = config.get("max_scenes_per_query", 10)
        self.scene_sampling_strategy = config.get("scene_sampling_strategy", "keyframes")
        
        # Result enhancement settings
        self.context_enrichment = config.get("context_enrichment", True)
        self.availability_lookup = config.get("availability_lookup", True)
        
        # Initialize metadata enrichment engine
        metadata_config = config.get("metadata_enrichment", {})
        self.metadata_enrichment_enabled = metadata_config.get("enabled", True)
        if self.metadata_enrichment_enabled:
            try:
                self.metadata_engine = MetadataEnrichmentEngine(metadata_config)
                logger.info(f"Metadata enrichment engine initialized with {len(self.metadata_engine.enrichers)} enrichers")
            except Exception as e:
                logger.error(f"Failed to initialize metadata enrichment engine: {e}")
                self.metadata_enrichment_enabled = False
        
        # Configure GPU if enabled
        if self.gpu_enabled:
            self._setup_gpu()
            
        logger.info(f"Initialized QueryProcessingEngine (GPU enabled: {self.gpu_enabled})")
        logger.info(f"Temporal alignment: {self.use_temporal_alignment}, Window: {self.alignment_window}s")
    
    async def preprocess_query(self, video_path: str) -> str:
        """Preprocess a query video for feature extraction.
        
        Args:
            video_path: Path to the query video
            
        Returns:
            Path to the preprocessed video
        """
        logger.info(f"Preprocessing query video: {video_path}")
        
        # Generate a unique ID for this query
        query_id = str(uuid.uuid4())
        output_path = os.path.join(self.temp_dir, f"{query_id}_processed.mp4")
        
        # For now, this is a placeholder for video preprocessing
        # In a real implementation, this would include:
        # - Enhancement
        # - Normalization
        # - Noise reduction
        # - Format standardization
        
        # For this example, we'll just copy the file
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Check if video opened successfully
            if not cap.isOpened():
                logger.error(f"Error opening video file: {video_path}")
                return video_path
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Scale down if the video is too large
            max_dimension = 480
            if width > max_dimension or height > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
            else:
                new_width, new_height = width, height
            
            # Create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
            
            # Process frames
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Resize frame
                if new_width != width or new_height != height:
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Apply basic enhancement
                # - Convert to LAB color space
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                # - Split channels
                l, a, b = cv2.split(lab)
                # - Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                # - Merge channels
                lab = cv2.merge((l, a, b))
                # - Convert back to BGR
                enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                
                # Write to output video
                out.write(enhanced)
            
            # Release resources
            cap.release()
            out.release()
            
            logger.info(f"Preprocessed video saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error preprocessing video: {e}")
            return video_path
    
    def _setup_gpu(self):
        """Configure the environment for GPU acceleration."""
        try:
            # Try to setup GPU acceleration for OpenCV
            cv2.setUseOptimized(True)
            
            # For feature extraction acceleration, attempt to use GPU if available
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = torch.device('cuda')
                    logger.info(f"GPU acceleration enabled with {torch.cuda.get_device_name(0)}")
                    
                    # Log GPU memory info
                    memory_allocated = torch.cuda.memory_allocated(0) / 1024**2  # MB
                    memory_reserved = torch.cuda.memory_reserved(0) / 1024**2  # MB
                    logger.info(f"GPU memory: {memory_allocated:.2f} MB allocated, {memory_reserved:.2f} MB reserved")
                else:
                    self.device = torch.device('cpu')
                    logger.warning("CUDA not available, falling back to CPU")
                    self.gpu_enabled = False
            except ImportError:
                logger.warning("PyTorch not available, GPU acceleration disabled")
                self.gpu_enabled = False
        except Exception as e:
            logger.error(f"Error setting up GPU acceleration: {e}")
            self.gpu_enabled = False
    
    async def extract_features(self, video_path: str) -> Dict[str, Any]:
        """Extract features from a preprocessed query video with GPU acceleration if enabled.
        
        Args:
            video_path: Path to the preprocessed video
            
        Returns:
            Dictionary of extracted features
        """
        logger.info(f"Extracting features from: {video_path}")
        
        # Use both visual and audio feature types for more accurate identification
        feature_types = [
            FeatureType.PERCEPTUAL_HASH,
            FeatureType.CNN_FEATURES,
            FeatureType.MOTION_PATTERN,
            FeatureType.AUDIO_SPECTROGRAM,  # Add audio features for multi-modal matching
        ]
        
        # Configure extraction options based on GPU availability
        extraction_options = {
            "use_gpu": self.gpu_enabled,
            "batch_size": self.batch_size,
            "sampling_strategy": self.scene_sampling_strategy,
            "max_scenes": self.max_scenes_per_query
        }
        
        # Add performance tracking
        start_time = time.time()
        features = self.feature_engine.process_full_video(
            video_path, 
            feature_types,
            **extraction_options
        )
        
        # Log performance metrics
        extraction_time = time.time() - start_time
        scene_count = len(features.get('scenes', []))
        logger.info(f"Extracted features from {scene_count} scenes in {extraction_time:.2f}s")
        logger.info(f"Average time per scene: {extraction_time/max(1, scene_count):.3f}s")
        
        return features
    
    async def retrieve_candidates(self, features: Dict[str, Any], top_k: int = 50) -> List[Dict[str, Any]]:
        """Retrieve candidate matches based on extracted features using vector database.
        
        Args:
            features: Dictionary of extracted features
            top_k: Number of candidate matches to retrieve
            
        Returns:
            List of candidate matches with scores
        """
        logger.info(f"Retrieving {top_k} candidates using vector search")
        
        # Get scenes from features
        scenes = features.get('scenes', [])
        if not scenes:
            logger.warning("No scenes found in features")
            return []
            
        # Use efficient scene sampling for faster retrieval
        sampled_scenes = self._sample_scenes(scenes)
        logger.info(f"Using {len(sampled_scenes)} representative scenes for retrieval")
        
        # Extract query vectors for each scene and feature type
        scene_candidates = []
        
        # Process each scene
        for scene_idx, scene in enumerate(sampled_scenes):
            # Prepare a dictionary of features for this scene
            scene_features = {}
            for feature_vector in scene.get('feature_vectors', []):
                feature_type = feature_vector.get('type')
                if feature_type and feature_vector.get('vector'):
                    # Convert feature type string to enum
                    try:
                        enum_type = FeatureType(feature_type)
                        scene_features[enum_type] = feature_vector.get('vector')
                    except (ValueError, KeyError):
                        logger.warning(f"Unknown feature type: {feature_type}")
            
            # Skip scenes with no usable features
            if not scene_features:
                continue
                
            # Find matches for this scene across various feature types
            try:
                # Use vector engine to find matches for this scene
                scene_matches = self.vector_query_engine.find_scene_matches(
                    scene_features=scene_features,
                    top_k=self.prefetch_candidates  # Get more candidates for better filtering
                )
                
                # Add scene timestamp information to the matches
                for match in scene_matches:
                    match['query_scene_idx'] = scene_idx
                    match['query_timestamp'] = scene.get('timestamp', 0)
                
                scene_candidates.extend(scene_matches)
            except Exception as e:
                logger.error(f"Error retrieving candidates for scene {scene_idx}: {e}")
        
        # Consolidate results across scenes using temporal alignment
        if self.use_temporal_alignment and len(scene_candidates) > 0:
            consolidated = self._consolidate_with_temporal_alignment(scene_candidates)
        else:
            # Just deduplicate and sort by score
            consolidated = self._consolidate_by_score(scene_candidates)
            
        logger.info(f"Retrieved {len(consolidated)} unique candidates")
        
        # Return top-k candidates
        return consolidated[:top_k]

    def _sample_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sample representative scenes for efficient retrieval.
        
        Args:
            scenes: List of scene dictionaries
            
        Returns:
            Sampled scenes list
        """
        # If we have fewer scenes than the limit, use all of them
        if len(scenes) <= self.max_scenes_per_query:
            return scenes
            
        # Different sampling strategies
        if self.scene_sampling_strategy == "uniform":
            # Uniform sampling across the video
            indices = np.linspace(0, len(scenes)-1, self.max_scenes_per_query, dtype=int)
            return [scenes[i] for i in indices]
        
        elif self.scene_sampling_strategy == "start_end_weighted":
            # Sample more from start and end (often more distinctive)
            num_start = self.max_scenes_per_query // 3
            num_end = self.max_scenes_per_query // 3
            num_middle = self.max_scenes_per_query - num_start - num_end
            
            # Get start scenes
            start_scenes = scenes[:num_start]
            
            # Get end scenes
            end_scenes = scenes[-num_end:] if num_end > 0 else []
            
            # Get middle scenes
            if num_middle > 0 and len(scenes) > (num_start + num_end):
                middle_indices = np.linspace(num_start, len(scenes)-num_end-1, num_middle, dtype=int)
                middle_scenes = [scenes[i] for i in middle_indices]
            else:
                middle_scenes = []
                
            return start_scenes + middle_scenes + end_scenes
        
        else:  # Default to keyframes (scenes with highest importance scores)
            # Sort by importance score if available
            scored_scenes = []
            for i, scene in enumerate(scenes):
                # Use importance score if available, otherwise use visual_interest or default to 0.5
                score = scene.get('importance', scene.get('visual_interest', 0.5))
                scored_scenes.append((i, score))
                
            # Sort by score descending
            scored_scenes.sort(key=lambda x: x[1], reverse=True)
            
            # Take top scenes
            indices = [i for i, _ in scored_scenes[:self.max_scenes_per_query]]
            indices.sort()  # Sort indices to maintain temporal order
            return [scenes[i] for i in indices]
            
    def _consolidate_with_temporal_alignment(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate candidates using temporal alignment to find consistent matches.
        
        Args:
            candidates: List of candidate matches from different scenes
            
        Returns:
            Consolidated list of candidates
        """
        # Group candidates by content_id
        content_groups = {}
        for candidate in candidates:
            content_id = candidate.get('content_id')
            if not content_id:
                continue
                
            if content_id not in content_groups:
                content_groups[content_id] = []
                
            content_groups[content_id].append(candidate)
            
        # Process each content group for temporal alignment
        aligned_results = []
        for content_id, matches in content_groups.items():
            # Skip if we only have one match (can't align)
            if len(matches) < 2:
                # Still include single matches but with lower confidence
                if matches:
                    match = matches[0].copy()
                    match['alignment_score'] = 0.0
                    aligned_results.append(match)
                continue
                
            # Sort by query timestamp
            matches.sort(key=lambda x: x.get('query_timestamp', 0))
            
            # Check for consistent temporal alignment
            # A good match should have consistent time offsets between query and target
            alignment_groups = []
            for i, match in enumerate(matches):
                # Get query and target timestamps
                query_time = match.get('query_timestamp', 0)
                target_time = match.get('timestamp')
                
                # Skip if target timestamp is not available
                if target_time is None:
                    continue
                    
                # Calculate offset
                offset = target_time - query_time
                
                # Find or create an alignment group for this offset
                found_group = False
                for group in alignment_groups:
                    group_offset = group['offset']
                    # Check if this offset is within our alignment window
                    if abs(offset - group_offset) <= self.alignment_window:
                        group['matches'].append(match)
                        # Update the average offset
                        group['offset'] = (group['offset'] * len(group['matches']) + offset) / (len(group['matches']) + 1)
                        found_group = True
                        break
                        
                if not found_group:
                    # Create a new alignment group
                    alignment_groups.append({
                        'offset': offset,
                        'matches': [match]
                    })
            
            # Find the largest alignment group
            if alignment_groups:
                best_group = max(alignment_groups, key=lambda g: len(g['matches']))
                
                # Only consider it a strong alignment if we have enough matching scenes
                if len(best_group['matches']) >= 2:
                    # Calculate average score across matches
                    scores = [m.get('score', 0) for m in best_group['matches']]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    
                    # Calculate alignment quality (0-1)
                    alignment_score = min(1.0, len(best_group['matches']) / len(matches))
                    
                    # Create consolidated result
                    best_match = max(best_group['matches'], key=lambda m: m.get('score', 0)).copy()
                    best_match['score'] = avg_score * (1 + alignment_score)  # Boost score based on alignment
                    best_match['alignment_score'] = alignment_score
                    best_match['aligned_scenes'] = len(best_group['matches'])
                    best_match['total_scenes'] = len(matches)
                    best_match['offset'] = best_group['offset']
                    
                    aligned_results.append(best_match)
                
        # Sort by score
        aligned_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return aligned_results

    def _consolidate_by_score(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple consolidation of candidates by highest score for each content_id.
        
        Args:
            candidates: List of candidate matches from different scenes
            
        Returns:
            Consolidated list of candidates
        """
        # Group by content_id and take highest scoring match
        best_matches = {}
        for candidate in candidates:
            content_id = candidate.get('content_id')
            if not content_id:
                continue
                
            score = candidate.get('score', 0)
            
            if content_id not in best_matches or score > best_matches[content_id].get('score', 0):
                best_matches[content_id] = candidate
                
        # Convert to list and sort by score
        results = list(best_matches.values())
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results
    
    async def detailed_matching(self, 
                           features: Dict[str, Any], 
                           candidates: List[Dict[str, Any]], 
                           top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform detailed matching with temporal alignment and multi-feature verification.
        
        Args:
            features: Dictionary of extracted features
            candidates: List of candidate matches from first-stage retrieval
            top_k: Number of final matches to return
            
        Returns:
            List of final matches with detailed information
        """
        logger.info(f"Performing detailed matching for {len(candidates)} candidates")
        
        # Start timing for performance tracking
        start_time = time.time()
        
        # Extract scenes for matching
        scenes = features.get('scenes', [])
        if not scenes:
            logger.warning("No scenes available for detailed matching")
            return self._convert_to_match_results(candidates[:top_k])
            
        # Process candidates concurrently for efficiency
        detailed_results = []
        
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Limit concurrent processing
        
        async def process_candidate(candidate):
            async with semaphore:
                try:
                    # Get content ID and other candidate info
                    content_id = candidate.get('content_id')
                    if not content_id:
                        return None
                        
                    # Initial confidence from vector search
                    initial_score = candidate.get('score', 0.0)
                    
                    # Use matching engine for detailed verification
                    # This can include frame-by-frame comparison, temporal verification, etc.
                    match_params = {
                        'content_id': content_id,
                        'query_features': features,
                        'algorithm': MatchingAlgorithm.ENSEMBLE,  # Use ensemble of algorithms
                        'temporal_verification': self.use_temporal_alignment,
                        'use_gpu': self.gpu_enabled
                    }
                    
                    # If we have alignment information from candidate retrieval, use it
                    if 'offset' in candidate:
                        match_params['time_offset'] = candidate.get('offset', 0)
                        
                    # Add alignment details if available
                    if 'alignment_score' in candidate:
                        match_params['alignment_score'] = candidate.get('alignment_score', 0)
                        match_params['aligned_scenes'] = candidate.get('aligned_scenes', 0)
                    
                    # Get detailed match result
                    if hasattr(self.matching_engine, 'verify_match'):
                        detailed_match = await self.matching_engine.verify_match(**match_params)
                        
                        # Enhance with metadata if available
                        if self.context_enrichment:
                            detailed_match = await self._enrich_match_result(detailed_match)
                            
                        return detailed_match
                    else:
                        # Fallback if matching engine doesn't have verify_match
                        return self._convert_to_match_result(candidate)
                        
                except Exception as e:
                    logger.error(f"Error in detailed matching for {content_id}: {e}")
                    return None
        
        # Create tasks for all candidates
        tasks = []
        for candidate in candidates:
            tasks.append(asyncio.create_task(process_candidate(candidate)))
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Filter out None results and sort by confidence
        detailed_results = [r for r in results if r is not None]
        detailed_results.sort(key=lambda x: x.confidence if isinstance(x, MatchResult) else x.get('confidence', 0), reverse=True)
        
        # Track processing time
        processing_time = time.time() - start_time
        logger.info(f"Detailed matching completed in {processing_time:.2f}s for {len(detailed_results)} results")
        
        # Return top results
        return detailed_results[:top_k]
    
    async def _enrich_match_result(self, match_result: Union[MatchResult, Dict[str, Any]]) -> Union[MatchResult, Dict[str, Any]]:
        """Enrich match results with additional metadata from multiple sources.
        
        Args:
            match_result: Match result to enrich
            
        Returns:
            Enriched match result with detailed metadata
        """
        # Handle both MatchResult objects and dictionaries
        if isinstance(match_result, MatchResult):
            content_id = match_result.content_id
            # Create a copy to avoid modifying the original
            result_dict = match_result.dict()
        else:
            content_id = match_result.get('content_id', '')
            # Create a copy to avoid modifying the original
            result_dict = match_result.copy()
            
        if not content_id:
            return match_result
        
        start_time = time.time()
        
        try:
            # Use the metadata enrichment engine if available
            if self.metadata_enrichment_enabled and hasattr(self, 'metadata_engine'):
                logger.debug(f"Using metadata enrichment engine for {content_id}")
                
                # Create base metadata from existing result
                base_metadata = {
                    "content_id": content_id,
                    "title": result_dict.get("title", "")
                }
                
                # Add any existing metadata fields
                if "additional_metadata" in result_dict:
                    base_metadata.update(result_dict["additional_metadata"])
                
                # Enrich with all available sources
                enriched_metadata = await self.metadata_engine.enrich_metadata(content_id, base_metadata)
                
                if enriched_metadata:
                    # Update title if improved
                    if not result_dict.get("title") and enriched_metadata.get("title"):
                        result_dict["title"] = enriched_metadata.get("title")
                        
                    # Create or update enriched metadata section
                    result_dict["enriched_metadata"] = enriched_metadata
                    
                    # Copy key fields to top level for convenience
                    for key in ["genres", "release_date", "runtime", "overview", "vote_average", "poster_url"]:
                        if key in enriched_metadata and key not in result_dict:
                            result_dict[key] = enriched_metadata[key]
                            
                    # Add formatted metadata for display
                    if "_sources" in enriched_metadata:
                        # Remove internal source tracking to clean up response
                        del enriched_metadata["_sources"]
            
            # Legacy enrichment path if metadata engine not available        
            elif hasattr(self, 'metadata_db_client') and self.metadata_db_client:
                metadata = await self.metadata_db_client.get_content_metadata(content_id)
                if metadata:
                    # Add or update metadata fields
                    result_dict['additional_metadata'] = {
                        **result_dict.get('additional_metadata', {}),
                        **metadata
                    }
                    
                    # Update title if not set
                    if not result_dict.get('title') and metadata.get('title'):
                        result_dict['title'] = metadata.get('title')
                        
                    # Add availability information if requested
                    if self.availability_lookup and hasattr(self.metadata_db_client, 'check_availability'):
                        availability = await self.metadata_db_client.check_availability(content_id)
                        if availability:
                            result_dict['availability'] = availability
            
            # Add temporal alignment information if available
            if result_dict.get('timestamp') is not None:
                timestamp = result_dict['timestamp']
                hours = int(timestamp // 3600)
                minutes = int((timestamp % 3600) // 60)
                seconds = int(timestamp % 60)
                result_dict["formatted_timestamp"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Log enrichment time for performance monitoring
            enrichment_time = time.time() - start_time
            if enrichment_time > 0.5:  # Only log if it took significant time
                logger.info(f"Metadata enrichment for {content_id} took {enrichment_time:.2f}s")
            
            # Convert dictionary back to MatchResult if original was MatchResult
            if isinstance(match_result, MatchResult):
                return MatchResult(**result_dict)
            else:
                return result_dict
                
        except Exception as e:
            logger.error(f"Error enriching match result for {content_id}: {e}")
            return match_result
            
    def _convert_to_match_result(self, candidate: Dict[str, Any]) -> MatchResult:
        """Convert a candidate dictionary to a MatchResult object.
        
        Args:
            candidate: Candidate dictionary
            
        Returns:
            MatchResult object
        """
        # Extract fields from candidate
        content_id = candidate.get('content_id', '')
        title = candidate.get('title', 'Unknown')
        score = candidate.get('score', 0.0)
        
        # Determine match type based on available info
        match_type = 'vector_match'
        if 'matched_features' in candidate:
            features = candidate.get('matched_features', [])
            if 'perceptual_hash' in features:
                match_type = 'hash_match'
            elif 'cnn_features' in features:
                match_type = 'visual_match'
            elif 'audio_spectrogram' in features or 'audio_fingerprint' in features:
                match_type = 'audio_match'
                
        # Add temporal info if available
        timestamp = candidate.get('timestamp')
        
        # Combine metadata
        metadata = {}
        if 'metadata' in candidate:
            metadata.update(candidate['metadata'])
        if 'alignment_score' in candidate:
            metadata['alignment_score'] = candidate['alignment_score']
        if 'aligned_scenes' in candidate:
            metadata['aligned_scenes'] = candidate['aligned_scenes']
            metadata['total_scenes'] = candidate.get('total_scenes', 0)
            
        # Create MatchResult
        return MatchResult(
            content_id=content_id,
            title=title,
            confidence=score,  # Use score as confidence
            match_type=match_type,
            timestamp=timestamp,
            additional_metadata=metadata
        )
        
    def _convert_to_match_results(self, candidates: List[Dict[str, Any]]) -> List[MatchResult]:
        """Convert a list of candidates to MatchResult objects.
        
        Args:
            candidates: List of candidate dictionaries
            
        Returns:
            List of MatchResult objects
        """
        return [self._convert_to_match_result(c) for c in candidates]
    
    async def process_query(self, 
                       video_path: str, 
                       algorithms: List[MatchingAlgorithm] = [MatchingAlgorithm.ENSEMBLE],
                       max_results: int = 5,
                       include_feature_data: bool = False) -> Dict[str, Any]:
        """Process a query from start to finish with optimized performance.
        
        Args:
            video_path: Path to the query video
            algorithms: List of matching algorithms to use
            max_results: Maximum number of results to return
            include_feature_data: Whether to include feature data in results
            
        Returns:
            Dictionary with query results and performance metrics
        """
        # Start overall timing
        start_time = time.time()
        logger.info(f"Processing query: {video_path}")
        
        # Create query result object
        query_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Performance metrics collection
        metrics = {
            "stages": {},
            "gpu_utilized": self.gpu_enabled,
            "batched_processing": True,
            "total_time": 0
        }
        
        try:
            # Step 1: Preprocess the query video
            stage_start = time.time()
            preprocessed_path = await self.preprocess_query(video_path)
            metrics["stages"]["preprocessing"] = time.time() - stage_start
            
            # Step 2: Extract features
            stage_start = time.time()
            features = await self.extract_features(preprocessed_path)
            extraction_time = time.time() - stage_start
            metrics["stages"]["feature_extraction"] = extraction_time
            metrics["scene_count"] = len(features.get("scenes", []))
            metrics["extraction_per_scene"] = extraction_time / max(1, metrics["scene_count"])
            
            # Step 3: Retrieve candidate matches
            stage_start = time.time()
            candidates = await self.retrieve_candidates(features, top_k=max_results*3)
            retrieval_time = time.time() - stage_start
            metrics["stages"]["candidate_retrieval"] = retrieval_time
            metrics["candidate_count"] = len(candidates)
            
            # Step 4: Perform detailed matching on candidates
            stage_start = time.time()
            detailed_matches = await self.detailed_matching(
                features, 
                candidates, 
                top_k=max_results*2
            )
            metrics["stages"]["detailed_matching"] = time.time() - stage_start
            
            # Step 5: Final result preparation and sorting
            stage_start = time.time()
            
            # Sort results by confidence
            if isinstance(detailed_matches[0], MatchResult) if detailed_matches else False:
                # If we have MatchResult objects
                results = sorted(detailed_matches, key=lambda x: x.confidence, reverse=True)[:max_results]
                
                # Convert to dictionaries for the response
                result_dicts = []
                for match in results:
                    match_dict = match.dict()
                    
                    # Format timestamps
                    if match.timestamp is not None:
                        hours = int(match.timestamp // 3600)
                        minutes = int((match.timestamp % 3600) // 60)
                        seconds = int(match.timestamp % 60)
                        match_dict["formatted_timestamp"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    result_dicts.append(match_dict)
                    
                results = result_dicts
            else:
                # If we already have dictionaries
                results = sorted(detailed_matches, key=lambda x: x.get("confidence", 0), reverse=True)[:max_results]
            
            metrics["stages"]["result_preparation"] = time.time() - stage_start
            metrics["match_count"] = len(results)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            metrics["total_time"] = total_time
            
            # Build complete response
            query_result = {
                "query_id": query_id,
                "timestamp": timestamp,
                "video_path": video_path,
                "processing_time": total_time,
                "performance_metrics": metrics,
                "results": results,
                "algorithms_used": [algo.value for algo in algorithms]
            }
            
            # Optionally include feature data (can be large)
            if include_feature_data:
                # Only include selected parts to avoid huge responses
                if "feature_vectors" in features:
                    # Limit feature vectors to reasonable size
                    feature_sample = {}
                    for feature_type, vectors in features["feature_vectors"].items():
                        # Just include a sample of each feature type
                        if isinstance(vectors, list) and len(vectors) > 0:
                            feature_sample[feature_type] = vectors[0] 
                    query_result["feature_sample"] = feature_sample
                    
                # Include scene count and types
                scene_info = {
                    "count": len(features.get("scenes", [])),
                    "feature_types": [scene.get("feature_types", []) for scene in features.get("scenes", [])[:3]]
                }
                query_result["scene_info"] = scene_info
            
            logger.info(f"Query processing completed in {total_time:.2f}s with {len(results)} results")
            return query_result
            
        except Exception as e:
            # Handle errors and include error information in the response
            error_time = time.time() - start_time
            logger.error(f"Error processing query: {e}")
            return {
                "query_id": query_id,
                "timestamp": timestamp,
                "video_path": video_path,
                "processing_time": error_time,
                "error": str(e),
                "status": "failed",
                "performance_metrics": metrics
            }
    
    async def batch_process_queries(self, 
                               query_paths: List[str], 
                               algorithms: List[MatchingAlgorithm] = [MatchingAlgorithm.ENSEMBLE],
                               max_results: int = 5) -> List[Dict[str, Any]]:
        """Process multiple queries in batch.
        
        Args:
            query_paths: List of paths to query videos
            algorithms: List of matching algorithms to use
            max_results: Maximum number of results to return per query
            
        Returns:
            List of query results
        """
        logger.info(f"Batch processing {len(query_paths)} queries")
        
        # Process queries concurrently
        tasks = [self.process_query(path, algorithms, max_results) for path in query_paths]
        results = await asyncio.gather(*tasks)
        
        return results
