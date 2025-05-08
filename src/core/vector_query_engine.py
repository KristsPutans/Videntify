"""Vector Query Engine

This module provides optimized vector search functionality to integrate with the query processing engine.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
import time

from src.db.milvus_fallback_adapter import MilvusFallbackAdapter
from src.core.feature_extraction import FeatureType

logger = logging.getLogger(__name__);

class VectorQueryEngine:
    """Engine for optimized vector-based querying."""
    
    def __init__(self, config: Dict[str, Any], vector_db_client=None):
        """Initialize the vector query engine.
        
        Args:
            config: Configuration dictionary
            vector_db_client: Client for the vector database
        """
        self.config = config
        self.vector_db_client = vector_db_client or MilvusFallbackAdapter(config.get("vector_db", {}))
        self.collection_name = config.get("collection_name", "videntify_videos")
        self.cache_enabled = config.get("cache_enabled", True)
        self.cache_ttl = config.get("cache_ttl", 3600)  # Cache TTL in seconds
        self.cache = {}
        self.cache_timestamps = {}
        
        # Query optimization parameters
        self.use_filtering = config.get("use_filtering", True)
        self.batch_size = config.get("batch_size", 32)
        
        logger.info(f"Initialized VectorQueryEngine with collection {self.collection_name}")
        logger.info(f"Cache enabled: {self.cache_enabled}, TTL: {self.cache_ttl}s")
    
    def _clean_cache(self):
        """Clean expired cache entries."""
        if not self.cache_enabled:
            return
            
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def query_by_feature(self, 
                         feature_type: FeatureType, 
                         feature_vector: List[float], 
                         top_k: int = 50,
                         filter_query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query the vector database by feature vector.
        
        Args:
            feature_type: Type of feature
            feature_vector: Feature vector to query
            top_k: Number of results to return
            filter_query: Optional filter query
            
        Returns:
            List of matching results
        """
        # Check cache first
        if self.cache_enabled:
            cache_key = f"{feature_type.value}_{hash(str(feature_vector))}_{top_k}_{hash(str(filter_query))}"
            if cache_key in self.cache:
                logger.debug(f"Cache hit for {feature_type.value} query")
                return self.cache[cache_key]
            
        # Prepare the query
        logger.info(f"Querying {feature_type.value} vector with top_k={top_k}")
        
        try:
            # Execute the search query
            search_params = {
                "metric_type": "L2",  # Use L2 distance for visual features
                "params": {"nprobe": 10}  # Number of clusters to search
            }
            
            if feature_type == FeatureType.PERCEPTUAL_HASH:
                # Use Hamming distance for hash-based features
                search_params["metric_type"] = "HAMMING"
            
            collection_name = self._get_collection_for_feature_type(feature_type)
            results = self.vector_db_client.search(
                collection_name=collection_name,
                query_vectors=[feature_vector],
                top_k=top_k,
                search_params=search_params
            )
            
            # Format the results
            if results and len(results) > 0:
                formatted_results = self._format_search_results(results[0], feature_type)
                
                # Cache the results
                if self.cache_enabled:
                    self.cache[cache_key] = formatted_results
                    self.cache_timestamps[cache_key] = time.time()
                    self._clean_cache()
                
                return formatted_results
            
            return []
            
        except Exception as e:
            logger.error(f"Error querying vector database: {e}")
            return []
    
    def _get_collection_for_feature_type(self, feature_type: FeatureType) -> str:
        """Get the appropriate collection name for a feature type.
        
        Args:
            feature_type: Type of feature
            
        Returns:
            Collection name
        """
        # Default to main collection
        base_collection = self.collection_name
        
        # Map feature types to specific collections if configured
        feature_collections = self.config.get("feature_collections", {})
        return feature_collections.get(feature_type.value, base_collection)
    
    def batch_query_by_features(self, 
                               feature_vectors: Dict[FeatureType, List[List[float]]],
                               top_k: int = 50) -> Dict[FeatureType, List[List[Dict[str, Any]]]]:
        """Batch query the vector database with multiple feature vectors.
        
        Args:
            feature_vectors: Dictionary mapping feature types to lists of vectors
            top_k: Number of results to return per query
            
        Returns:
            Dictionary mapping feature types to lists of results lists
        """
        logger.info(f"Batch querying with {sum(len(vecs) for vecs in feature_vectors.values())} vectors")
        
        results = {}
        
        for feature_type, vectors in feature_vectors.items():
            feature_results = []
            
            # Process in batches
            for i in range(0, len(vectors), self.batch_size):
                batch = vectors[i:i+self.batch_size]
                logger.debug(f"Processing batch of {len(batch)} {feature_type.value} vectors")
                
                search_params = {
                    "metric_type": "L2",
                    "params": {"nprobe": 10}
                }
                
                if feature_type == FeatureType.PERCEPTUAL_HASH:
                    search_params["metric_type"] = "HAMMING"
                
                try:
                    collection_name = self._get_collection_for_feature_type(feature_type)
                    batch_results = self.vector_db_client.search(
                        collection_name=collection_name,
                        query_vectors=batch,
                        top_k=top_k,
                        search_params=search_params
                    )
                    
                    # Format the results
                    formatted_batch_results = [
                        self._format_search_results(res, feature_type) for res in batch_results
                    ]
                    feature_results.extend(formatted_batch_results)
                    
                except Exception as e:
                    logger.error(f"Error in batch query for {feature_type.value}: {e}")
                    # Add empty results for the failed batch
                    feature_results.extend([[] for _ in range(len(batch))])
            
            results[feature_type] = feature_results
        
        return results
    
    def _format_search_results(self, search_results: List[Dict[str, Any]], feature_type: FeatureType) -> List[Dict[str, Any]]:
        """Format search results into a standardized structure.
        
        Args:
            search_results: Raw search results from the vector database
            feature_type: Type of feature that was queried
            
        Returns:
            Formatted results list
        """
        formatted_results = []
        
        for result in search_results:
            # Get metadata to extract content information
            metadata = result.get("metadata", {})
            # Convert string metadata to dict if necessary
            if isinstance(metadata, str):
                try:
                    import json
                    metadata = json.loads(metadata)
                except:
                    metadata = {"raw": metadata}
            
            # Map database result to standardized format
            formatted_result = {
                "content_id": str(result.get("id")),
                "score": result.get("score", 0.0),
                "distance": result.get("distance", 0.0),
                "feature_type": feature_type.value,
                "metadata": metadata,
                "video_id": metadata.get("video_id", str(result.get("id"))),
                "title": metadata.get("title", "Unknown"),
                "timestamp": metadata.get("timestamp")
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def find_scene_matches(self, 
                          scene_features: Dict[FeatureType, List[float]], 
                          top_k: int = 10) -> List[Dict[str, Any]]:
        """Find matches for a single scene across multiple feature types.
        
        Args:
            scene_features: Dictionary mapping feature types to vectors
            top_k: Number of results to return
            
        Returns:
            List of consolidated results across feature types
        """
        logger.info(f"Finding matches for scene with {len(scene_features)} feature types")
        
        all_matches = {}
        feature_weights = {
            FeatureType.CNN_FEATURES: 0.5,
            FeatureType.PERCEPTUAL_HASH: 0.3,
            FeatureType.MOTION_PATTERN: 0.2,
            FeatureType.AUDIO_SPECTROGRAM: 0.3,
            FeatureType.AUDIO_FINGERPRINT: 0.2
        }
        
        # Query for each feature type
        for feature_type, vector in scene_features.items():
            matches = self.query_by_feature(
                feature_type=feature_type,
                feature_vector=vector,
                top_k=top_k * 2  # Get more candidates for better consolidation
            )
            
            # Weight for this feature type
            weight = feature_weights.get(feature_type, 0.1)
            
            # Add to consolidated results with weighting
            for match in matches:
                content_id = match["content_id"]
                score = match["score"] * weight
                
                if content_id in all_matches:
                    all_matches[content_id]["score"] += score
                    all_matches[content_id]["matched_features"].append(feature_type.value)
                else:
                    all_matches[content_id] = {
                        "content_id": content_id,
                        "score": score,
                        "video_id": match["video_id"],
                        "title": match["title"],
                        "matched_features": [feature_type.value],
                        "timestamp": match.get("timestamp")
                    }
        
        # Sort by overall score
        results = list(all_matches.values())
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def close(self):
        """Close connections and clean up resources."""
        try:
            if hasattr(self, 'vector_db_client') and hasattr(self.vector_db_client, 'disconnect'):
                self.vector_db_client.disconnect()
        except Exception as e:
            logger.error(f"Error closing vector query engine: {e}")
