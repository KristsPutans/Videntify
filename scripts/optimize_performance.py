#!/usr/bin/env python3
"""
Performance Optimization Script for Videntify

This script provides tools to optimize performance of the Videntify system:
1. GPU acceleration for the feature extraction and matching pipelines
2. Benchmark and optimize query performance
3. Cache configuration for frequent operations
"""

import os
import sys
import time
import json
import argparse
import numpy as np
from tqdm import tqdm
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import Videntify modules
from src.config.config import ConfigManager
from src.core.feature_extraction import FeatureType
from src.core.vector_db_integration import VectorDBIntegration
from src.core.matching_engine import MatchingEngine, MatchingAlgorithm


class PerformanceOptimizer:
    """Performance optimizer for Videntify system."""
    
    def __init__(self):
        """Initialize the performance optimizer."""
        self.config_manager = ConfigManager()
        self.vector_db = VectorDBIntegration()
        self.matching_engine = MatchingEngine({"match_threshold": 0.7})
        
        # Default values
        self.num_samples = 10
        self.batch_size = 4
        self.results_dir = project_root / "benchmarks"
        self.results_dir.mkdir(exist_ok=True)
    
    def check_gpu_availability(self) -> bool:
        """Check if GPU is available for acceleration."""
        try:
            import torch
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_count = torch.cuda.device_count()
                print(f"u2705 GPU available: {gpu_name} (Count: {gpu_count})")
            else:
                print("u274c No GPU available for acceleration")
            return gpu_available
        except ImportError:
            print("u274c PyTorch not installed. Install via: pip install torch")
            return False
        except Exception as e:
            print(f"u274c Error checking GPU availability: {e}")
            return False
    
    def enable_gpu_acceleration(self) -> bool:
        """Enable GPU acceleration for feature extraction and matching."""
        if not self.check_gpu_availability():
            return False
        
        try:
            # Update config to enable GPU
            feature_extraction_config = self.config_manager.get("feature_extraction", {})
            feature_extraction_config["use_gpu"] = True
            self.config_manager.set("feature_extraction", feature_extraction_config)
            
            matching_config = self.config_manager.get("matching_engine", {})
            matching_config["use_gpu"] = True
            self.config_manager.set("matching_engine", matching_config)
            
            self.config_manager.save()
            print("u2705 GPU acceleration enabled in configuration")
            
            # Verify models can run on GPU
            self._verify_gpu_models()
            return True
        except Exception as e:
            print(f"u274c Error enabling GPU acceleration: {e}")
            return False
    
    def _verify_gpu_models(self) -> bool:
        """Verify that models can run on GPU."""
        try:
            import torch
            # Check if pytorch can access the GPU
            if torch.cuda.is_available():
                # Create a small tensor and move it to GPU
                tensor = torch.rand(10, 10)
                tensor = tensor.cuda()
                print(f"u2705 PyTorch can access GPU: {tensor.device}")
                return True
            return False
        except Exception as e:
            print(f"u274c Error verifying GPU models: {e}")
            return False
    
    def benchmark_feature_extraction(self, video_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Benchmark feature extraction performance.
        
        Args:
            video_paths: List of paths to test videos. If None, random data will be used.
            
        Returns:
            Dictionary with benchmark results
        """
        from src.core.feature_extraction import (
            CNNFeatureExtractor,
            PerceptualHashExtractor,
            MotionFeatureExtractor,
            MFCCExtractor
        )
        
        print(f"\nBenchmarking feature extraction performance...")
        
        # Use test videos if provided, otherwise generate random data
        if not video_paths:
            print("No video paths provided, using random test data")
            # We'll simulate the feature extraction with random data
            results = self._benchmark_feature_extraction_with_random_data()
        else:
            # TODO: Implement real video feature extraction benchmarking
            print("Real video feature extraction benchmarking not implemented yet")
            results = {}
        
        # Save results
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        results_file = self.results_dir / f"feature_extraction_benchmark_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"u2705 Benchmark results saved to {results_file}")
        return results
    
    def _benchmark_feature_extraction_with_random_data(self) -> Dict[str, Any]:
        """Benchmark feature extraction with random data."""
        import torch
        import time
        
        extractors = {
            "CNN": (CNNFeatureExtractor, (224, 224, 3)),
            "PerceptualHash": (PerceptualHashExtractor, (64, 64, 3)),
            "Motion": (MotionFeatureExtractor, (224, 224, 3)),
            "MFCC": (MFCCExtractor, (13, 100)) # 13 MFCCs, 100 frames
        }
        
        results = {}
        use_gpu = self.config_manager.get("feature_extraction", {}).get("use_gpu", False)
        
        for name, (extractor_class, input_shape) in extractors.items():
            try:
                # Initialize the extractor
                extractor = extractor_class({"use_gpu": use_gpu})
                
                # Create random inputs based on shape
                if name != "MFCC":
                    # For image-based extractors
                    inputs = [np.random.rand(*input_shape).astype(np.float32) for _ in range(self.num_samples)]
                else:
                    # For audio-based extractors
                    inputs = [np.random.rand(*input_shape).astype(np.float32) for _ in range(self.num_samples)]
                
                # Single extraction time
                start_time = time.time()
                for inp in inputs:
                    if name != "MFCC":
                        extractor.extract_features(inp)
                    else:
                        extractor.extract_features(inp)
                single_time = (time.time() - start_time) / self.num_samples
                
                # Batch extraction time if supported
                batch_time = None
                if hasattr(extractor, "extract_features_batch"):
                    # Split inputs into batches
                    batches = [inputs[i:i+self.batch_size] for i in range(0, len(inputs), self.batch_size)]
                    
                    start_time = time.time()
                    for batch in batches:
                        extractor.extract_features_batch(batch)
                    batch_time = (time.time() - start_time) / len(batches)
                
                results[name] = {
                    "single_sample_time": single_time,
                    "batch_time": batch_time,
                    "batch_size": self.batch_size,
                    "speedup": None if batch_time is None else (single_time * self.batch_size) / batch_time,
                    "device": "GPU" if use_gpu and torch.cuda.is_available() else "CPU"
                }
                
                print(f"u2705 {name} Extractor: {single_time:.4f}s per sample, Device: {results[name]['device']}")
                if batch_time:
                    print(f"  u2192 Batch processing: {batch_time:.4f}s per batch, Speedup: {results[name]['speedup']:.2f}x")
            
            except Exception as e:
                print(f"u274c Error benchmarking {name} extractor: {e}")
                results[name] = {"error": str(e)}
        
        return results
    
    def benchmark_vector_search(self, num_queries: int = 10) -> Dict[str, Any]:
        """Benchmark vector search performance.
        
        Args:
            num_queries: Number of queries to run
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"\nBenchmarking vector search performance...")
        
        results = {}
        feature_types = [
            (FeatureType.CNN_FEATURES, 2048),
            (FeatureType.PERCEPTUAL_HASH, 64),
            (FeatureType.MOTION_PATTERN, 256),
            (FeatureType.AUDIO_SPECTROGRAM, 512)
        ]
        
        for feature_type, dimension in feature_types:
            print(f"Testing {feature_type.name} ({dimension} dimensions)...")
            search_times = []
            
            try:
                # Create a collection name based on feature type
                collection_name = f"vidid_{feature_type.value}"
                
                # Check if collection exists
                if not self.vector_db.vector_db_client.collection_exists(collection_name):
                    print(f"  u2139ufe0f Creating collection {collection_name}...")
                    self.vector_db.vector_db_client.create_collection(collection_name, dimension)
                    
                    # Insert some random vectors for testing
                    num_vectors = 100
                    print(f"  u2139ufe0f Inserting {num_vectors} random vectors...")
                    vectors = np.random.rand(num_vectors, dimension).astype(np.float32)
                    ids = [f"test_vector_{i}" for i in range(num_vectors)]
                    metadata = [{"source": "benchmark", "index": i} for i in range(num_vectors)]
                    
                    self.vector_db.vector_db_client.insert_vectors(collection_name, vectors, ids, metadata)
                
                # Generate query vectors
                query_vectors = np.random.rand(num_queries, dimension).astype(np.float32)
                
                # Time search operations
                for i in range(num_queries):
                    query_vector = query_vectors[i]
                    
                    start_time = time.time()
                    self.vector_db.vector_db_client.search_vectors(
                        collection_name,
                        [query_vector.tolist()],
                        top_k=10
                    )
                    elapsed_time = time.time() - start_time
                    search_times.append(elapsed_time)
                
                # Calculate statistics
                results[feature_type.name] = {
                    "dimension": dimension,
                    "avg_search_time": sum(search_times) / len(search_times),
                    "min_search_time": min(search_times),
                    "max_search_time": max(search_times),
                    "queries_per_second": len(search_times) / sum(search_times)
                }
                
                print(f"  u2705 Average search time: {results[feature_type.name]['avg_search_time']:.4f}s")
                print(f"  u2705 Queries per second: {results[feature_type.name]['queries_per_second']:.2f}")
            
            except Exception as e:
                print(f"  u274c Error: {e}")
                results[feature_type.name] = {"error": str(e)}
        
        # Save results
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        results_file = self.results_dir / f"vector_search_benchmark_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"u2705 Benchmark results saved to {results_file}")
        return results
    
    def optimize_query_pipeline(self) -> bool:
        """Optimize the query pipeline based on benchmark results."""
        print(f"\nOptimizing query pipeline...")
        
        try:
            # Update vector database search parameters
            vector_db_config = self.config_manager.get("vector_db", {})
            
            # Adjust search parameters based on database type
            if vector_db_config.get("type") == "milvus":
                print("u2139ufe0f Optimizing parameters for Milvus")
                
                # Optimize IVF index parameters
                if "index_params" not in vector_db_config:
                    vector_db_config["index_params"] = {}
                
                vector_db_config["index_params"]["index_type"] = "IVF_FLAT"  # Good balance of speed and accuracy
                vector_db_config["index_params"]["params"] = {"nlist": 1024}  # Number of clusters
                
                # Optimize search parameters
                if "search_params" not in vector_db_config:
                    vector_db_config["search_params"] = {}
                
                vector_db_config["search_params"]["params"] = {"nprobe": 16}  # Number of clusters to search
                
                # Set up connection pooling for better performance
                vector_db_config["connection_pool_size"] = 10
            
            elif vector_db_config.get("type") == "pinecone":
                print("u2139ufe0f Optimizing parameters for Pinecone")
                # Pinecone manages most optimizations internally
                pass
            
            # Update the configuration
            self.config_manager.set("vector_db", vector_db_config)
            
            # Optimize matching engine parameters
            matching_config = self.config_manager.get("matching_engine", {})
            
            # Enable batching for similarity calculations
            matching_config["enable_batching"] = True
            matching_config["batch_size"] = 16  # Process 16 comparisons at a time
            
            # Set up caching for frequent operations
            matching_config["cache_results"] = True
            matching_config["cache_size"] = 1000  # Cache 1000 recent results
            
            # Update the configuration
            self.config_manager.set("matching_engine", matching_config)
            
            # Save all configuration changes
            self.config_manager.save()
            
            print("u2705 Query pipeline optimization completed")
            return True
        except Exception as e:
            print(f"u274c Error optimizing query pipeline: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Performance Optimization Script for Videntify")
    parser.add_argument("--check-gpu", action="store_true", help="Check if GPU is available")
    parser.add_argument("--enable-gpu", action="store_true", help="Enable GPU acceleration")
    parser.add_argument("--benchmark-extraction", action="store_true", help="Benchmark feature extraction")
    parser.add_argument("--benchmark-search", action="store_true", help="Benchmark vector search")
    parser.add_argument("--optimize-query", action="store_true", help="Optimize query pipeline")
    parser.add_argument("--all", action="store_true", help="Run all optimizations")
    
    args = parser.parse_args()
    
    # Default to --check-gpu if no arguments provided
    if not any(vars(args).values()):
        args.check_gpu = True
    
    print("=== Videntify Performance Optimization ===\n")
    
    optimizer = PerformanceOptimizer()
    
    if args.check_gpu or args.all:
        print("\nud83dudccb Checking GPU availability...")
        optimizer.check_gpu_availability()
    
    if args.enable_gpu or args.all:
        print("\nud83dudccb Enabling GPU acceleration...")
        optimizer.enable_gpu_acceleration()
    
    if args.benchmark_extraction or args.all:
        print("\nud83dudccb Benchmarking feature extraction...")
        optimizer.benchmark_feature_extraction()
    
    if args.benchmark_search or args.all:
        print("\nud83dudccb Benchmarking vector search...")
        optimizer.benchmark_vector_search()
    
    if args.optimize_query or args.all:
        print("\nud83dudccb Optimizing query pipeline...")
        optimizer.optimize_query_pipeline()
    
    print("\nu2705 Performance optimization completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
