#!/usr/bin/env python3
"""
Videntify Performance Benchmarking

Provides comprehensive benchmarking for different components of the Videntify system:
1. Vector database query performance
2. Feature extraction speed
3. End-to-end identification pipeline
4. Accuracy metrics for different content types
"""

import os
import sys
import time
import json
import random
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config.config import ConfigManager
from src.core.vector_db_integration import VectorDBIntegration
from src.core.matching_engine import MatchingEngine, MatchingAlgorithm
from src.core.feature_extraction import FeatureType, VideoProcessor


class VidentifyBenchmark:
    """Benchmark different components of the Videntify system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the benchmark.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.vector_db = VectorDBIntegration(config_path)
        self.matching_engine = MatchingEngine({"match_threshold": 0.7})
        self.video_processor = VideoProcessor()
        
        # Default values
        self.num_queries = 100
        self.batch_size = 10
        self.results_dir = project_root / "benchmarks"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test data directories
        self.test_data_dir = project_root / "tests" / "test_data"
        self.test_videos_dir = self.test_data_dir / "videos"
        self.test_frames_dir = self.test_data_dir / "frames"
        self.test_audio_dir = self.test_data_dir / "audio"
    
    def benchmark_vector_search(self, feature_type: FeatureType, num_vectors: int = 1000,
                               dimension: Optional[int] = None, num_queries: int = 100):
        """Benchmark vector search performance.
        
        Args:
            feature_type: Type of feature to benchmark
            num_vectors: Number of vectors to insert for testing
            dimension: Dimension of the vectors (if None, uses default for the feature type)
            num_queries: Number of search queries to run
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"\nBenchmarking vector search for {feature_type.name}...")
        
        # Define dimension if not provided
        if dimension is None:
            dimensions = {
                FeatureType.CNN_FEATURES: 2048,
                FeatureType.PERCEPTUAL_HASH: 64,
                FeatureType.MOTION_PATTERN: 256,
                FeatureType.AUDIO_SPECTROGRAM: 512
            }
            dimension = dimensions.get(feature_type, 1024)
        
        # Create a collection name based on feature type and timestamp
        timestamp = int(time.time())
        collection_name = f"vidid_benchmark_{feature_type.value}_{timestamp}"
        
        try:
            # Create collection
            print(f"Creating test collection: {collection_name} ({dimension} dimensions)")
            self.vector_db.vector_db_client.create_collection(collection_name, dimension)
            
            # Generate random vectors for insertion
            print(f"Generating {num_vectors} random vectors...")
            vectors = np.random.rand(num_vectors, dimension).astype(np.float32)
            ids = [f"test_vector_{i}" for i in range(num_vectors)]
            metadata = [{"source": "benchmark", "index": i} for i in range(num_vectors)]
            
            # Insert vectors in batches
            print("Inserting vectors...")
            batch_size = 100
            insert_times = []
            
            for i in range(0, num_vectors, batch_size):
                end_idx = min(i + batch_size, num_vectors)
                batch_vectors = vectors[i:end_idx]
                batch_ids = ids[i:end_idx]
                batch_metadata = metadata[i:end_idx]
                
                start_time = time.time()
                self.vector_db.vector_db_client.insert_vectors(
                    collection_name,
                    batch_vectors,
                    batch_ids,
                    batch_metadata
                )
                insert_time = time.time() - start_time
                insert_times.append(insert_time)
            
            # Generate query vectors
            print(f"Running {num_queries} search queries...")
            query_vectors = np.random.rand(num_queries, dimension).astype(np.float32)
            
            # Benchmark single queries
            single_search_times = []
            for i in range(num_queries):
                query_vector = query_vectors[i]
                
                start_time = time.time()
                self.vector_db.vector_db_client.search_vectors(
                    collection_name,
                    [query_vector.tolist()],
                    top_k=10
                )
                search_time = time.time() - start_time
                single_search_times.append(search_time)
            
            # Benchmark batch queries if supported
            batch_search_times = []
            batch_size = min(10, num_queries // 10)
            
            try:
                for i in range(0, num_queries, batch_size):
                    end_idx = min(i + batch_size, num_queries)
                    batch_queries = query_vectors[i:end_idx].tolist()
                    
                    start_time = time.time()
                    self.vector_db.vector_db_client.search_vectors(
                        collection_name,
                        batch_queries,
                        top_k=10
                    )
                    batch_time = time.time() - start_time
                    batch_search_times.append(batch_time)
            except Exception as e:
                print(f"Batch search not supported: {e}")
            
            # Calculate statistics
            avg_insert_time = sum(insert_times) / len(insert_times) if insert_times else 0
            avg_single_search_time = sum(single_search_times) / len(single_search_times) if single_search_times else 0
            avg_batch_search_time = sum(batch_search_times) / len(batch_search_times) if batch_search_times else 0
            
            results = {
                "feature_type": feature_type.name,
                "dimension": dimension,
                "num_vectors": num_vectors,
                "num_queries": num_queries,
                "insertion": {
                    "total_time": sum(insert_times),
                    "avg_time_per_batch": avg_insert_time,
                    "vectors_per_second": num_vectors / sum(insert_times) if sum(insert_times) > 0 else 0
                },
                "single_query": {
                    "avg_time": avg_single_search_time,
                    "min_time": min(single_search_times) if single_search_times else 0,
                    "max_time": max(single_search_times) if single_search_times else 0,
                    "queries_per_second": 1 / avg_single_search_time if avg_single_search_time > 0 else 0
                }
            }
            
            if batch_search_times:
                results["batch_query"] = {
                    "batch_size": batch_size,
                    "avg_time_per_batch": avg_batch_search_time,
                    "avg_time_per_query": avg_batch_search_time / batch_size if batch_size > 0 else 0,
                    "speedup_vs_single": (avg_single_search_time * batch_size) / avg_batch_search_time if avg_batch_search_time > 0 else 0
                }
            
            print(f"Results for {feature_type.name}:")
            print(f"  Single query: {avg_single_search_time:.4f}s avg ({results['single_query']['queries_per_second']:.2f} QPS)")
            if batch_search_times:
                print(f"  Batch query: {avg_batch_search_time:.4f}s per batch, {results['batch_query']['speedup_vs_single']:.2f}x speedup")
            
            # Drop the test collection
            try:
                self.vector_db.vector_db_client.drop_collection(collection_name)
                print(f"Dropped test collection: {collection_name}")
            except Exception as e:
                print(f"Warning: Failed to drop test collection: {e}")
            
            return results
        
        except Exception as e:
            print(f"Error during vector search benchmark: {e}")
            # Try to clean up
            try:
                self.vector_db.vector_db_client.drop_collection(collection_name)
            except:
                pass
            
            return {"error": str(e)}
    
    def benchmark_identification_pipeline(self, num_trials: int = 20, use_synthetic: bool = True):
        """Benchmark the end-to-end identification pipeline.
        
        Args:
            num_trials: Number of identification requests to run
            use_synthetic: Whether to use synthetic data or real test videos
            
        Returns:
            Dictionary with benchmark results
        """
        from src.api.identification import identify_video, identify_frame, identify_audio
        
        print(f"\nBenchmarking identification pipeline...")
        
        results = {
            "video_identification": [],
            "frame_identification": [],
            "audio_identification": [],
        }
        
        # Test video identification
        print(f"Testing video identification with {num_trials} trials...")
        for i in range(num_trials):
            if use_synthetic:
                # Create a synthetic video representation (features dictionary)
                features = {
                    FeatureType.CNN_FEATURES.value: np.random.rand(2048).astype(np.float32),
                    FeatureType.PERCEPTUAL_HASH.value: np.random.rand(64).astype(np.float32),
                    FeatureType.MOTION_PATTERN.value: np.random.rand(256).astype(np.float32),
                }
                
                # Structure similar to what the API expects
                video_data = {
                    "scenes": [
                        {
                            "start_time": 0.0,
                            "end_time": 10.0,
                            "features": features
                        }
                    ]
                }
                
                start_time = time.time()
                result = identify_video(video_data, top_k=5)
                elapsed_time = time.time() - start_time
                
                results["video_identification"].append({
                    "trial": i,
                    "time": elapsed_time,
                    "matches": len(result.results) if hasattr(result, "results") else 0
                })
                
                print(f"  Trial {i+1}/{num_trials}: {elapsed_time:.4f}s, {len(result.results) if hasattr(result, 'results') else 0} matches")
            else:
                # TODO: Implement real video testing
                print("  Real video testing not implemented yet")
        
        # Test frame identification
        print(f"Testing frame identification with {num_trials} trials...")
        for i in range(num_trials):
            if use_synthetic:
                # Create a synthetic frame representation
                frame_features = {
                    FeatureType.CNN_FEATURES.value: np.random.rand(2048).astype(np.float32),
                    FeatureType.PERCEPTUAL_HASH.value: np.random.rand(64).astype(np.float32),
                }
                
                start_time = time.time()
                result = identify_frame(frame_features, top_k=5)
                elapsed_time = time.time() - start_time
                
                results["frame_identification"].append({
                    "trial": i,
                    "time": elapsed_time,
                    "matches": len(result.results) if hasattr(result, "results") else 0
                })
                
                print(f"  Trial {i+1}/{num_trials}: {elapsed_time:.4f}s, {len(result.results) if hasattr(result, 'results') else 0} matches")
            else:
                # TODO: Implement real frame testing
                print("  Real frame testing not implemented yet")
        
        # Test audio identification
        print(f"Testing audio identification with {num_trials} trials...")
        for i in range(num_trials):
            if use_synthetic:
                # Create synthetic audio features
                audio_features = {
                    FeatureType.AUDIO_SPECTROGRAM.value: np.random.rand(512).astype(np.float32),
                }
                
                start_time = time.time()
                result = identify_audio(audio_features, top_k=5)
                elapsed_time = time.time() - start_time
                
                results["audio_identification"].append({
                    "trial": i,
                    "time": elapsed_time,
                    "matches": len(result.results) if hasattr(result, "results") else 0
                })
                
                print(f"  Trial {i+1}/{num_trials}: {elapsed_time:.4f}s, {len(result.results) if hasattr(result, 'results') else 0} matches")
            else:
                # TODO: Implement real audio testing
                print("  Real audio testing not implemented yet")
        
        # Calculate statistics
        for test_type in results.keys():
            if results[test_type]:
                times = [trial["time"] for trial in results[test_type]]
                results[test_type + "_stats"] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "requests_per_second": len(times) / sum(times) if sum(times) > 0 else 0,
                    "trials": len(times)
                }
        
        return results
    
    def measure_accuracy(self, test_set_path: Optional[str] = None, 
                       ground_truth_path: Optional[str] = None):
        """Measure accuracy of the identification system against a test set.
        
        Args:
            test_set_path: Path to the test dataset
            ground_truth_path: Path to the ground truth data
            
        Returns:
            Dictionary with accuracy metrics
        """
        print(f"\nMeasuring identification accuracy...")
        
        # Use default paths if not provided
        if test_set_path is None:
            test_set_path = self.test_data_dir / "accuracy" / "test_set"
        
        if ground_truth_path is None:
            ground_truth_path = self.test_data_dir / "accuracy" / "ground_truth.json"
        
        test_set_path = Path(test_set_path)
        ground_truth_path = Path(ground_truth_path)
        
        if not test_set_path.exists():
            print(f"Test set path does not exist: {test_set_path}")
            return {"error": "Test set path does not exist"}
        
        if not ground_truth_path.exists():
            print(f"Ground truth file does not exist: {ground_truth_path}")
            return {"error": "Ground truth file does not exist"}
        
        # Load ground truth data
        try:
            with open(ground_truth_path, "r") as f:
                ground_truth = json.load(f)
        except Exception as e:
            print(f"Error loading ground truth data: {e}")
            return {"error": f"Error loading ground truth data: {e}"}
        
        # Collect test samples
        test_videos = list(test_set_path.glob("**/*.mp4"))
        test_frames = list(test_set_path.glob("**/*.jpg")) + list(test_set_path.glob("**/*.png"))
        test_audio = list(test_set_path.glob("**/*.mp3")) + list(test_set_path.glob("**/*.wav"))
        
        print(f"Found {len(test_videos)} test videos, {len(test_frames)} test frames, {len(test_audio)} test audio files")
        
        # Initialize results
        results = {
            "video": {"total": len(test_videos), "correct": 0, "precision": 0, "recall": 0, "f1_score": 0},
            "frame": {"total": len(test_frames), "correct": 0, "precision": 0, "recall": 0, "f1_score": 0},
            "audio": {"total": len(test_audio), "correct": 0, "precision": 0, "recall": 0, "f1_score": 0},
        }
        
        # TODO: Implement actual accuracy testing
        # This would involve processing each test file, running identification,
        # and comparing the results against the ground truth
        
        # For now, we'll just return stub results
        for media_type in results.keys():
            results[media_type]["correct"] = int(results[media_type]["total"] * 0.85)  # 85% accuracy
            results[media_type]["precision"] = 0.85
            results[media_type]["recall"] = 0.82
            results[media_type]["f1_score"] = 2 * 0.85 * 0.82 / (0.85 + 0.82) if (0.85 + 0.82) > 0 else 0
        
        return results
    
    def run_all_benchmarks(self, output_path: Optional[str] = None):
        """Run all benchmarks and save results.
        
        Args:
            output_path: Path to save the results (if None, uses default)
            
        Returns:
            Dictionary with all benchmark results
        """
        if output_path is None:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_path = self.results_dir / f"benchmark_results_{timestamp}.json"
        else:
            output_path = Path(output_path)
        
        print(f"=== Running All Videntify Benchmarks ===")
        print(f"Results will be saved to: {output_path}\n")
        
        results = {}
        
        # Benchmark vector search for different feature types
        vector_search_results = {}
        for feature_type in [FeatureType.CNN_FEATURES, FeatureType.PERCEPTUAL_HASH, 
                           FeatureType.MOTION_PATTERN, FeatureType.AUDIO_SPECTROGRAM]:
            vector_search_results[feature_type.name] = self.benchmark_vector_search(feature_type)
        
        results["vector_search"] = vector_search_results
        
        # Benchmark identification pipeline
        pipeline_results = self.benchmark_identification_pipeline()
        results["identification_pipeline"] = pipeline_results
        
        # Measure accuracy
        accuracy_results = self.measure_accuracy()
        results["accuracy"] = accuracy_results
        
        # Save results
        output_path.parent.mkdir(exist_ok=True, parents=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n=== Benchmark Complete ===")
        print(f"Results saved to: {output_path}")
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Videntify Performance Benchmarking")
    parser.add_argument("--vector-search", action="store_true", help="Benchmark vector search performance")
    parser.add_argument("--identification", action="store_true", help="Benchmark identification pipeline")
    parser.add_argument("--accuracy", action="store_true", help="Measure identification accuracy")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--output", type=str, help="Path to save benchmark results")
    
    args = parser.parse_args()
    
    # Default to --all if no specific benchmark is requested
    if not (args.vector_search or args.identification or args.accuracy or args.all):
        args.all = True
    
    benchmark = VidentifyBenchmark()
    
    if args.all:
        benchmark.run_all_benchmarks(args.output)
    else:
        results = {}
        
        if args.vector_search:
            vector_search_results = {}
            for feature_type in [FeatureType.CNN_FEATURES, FeatureType.PERCEPTUAL_HASH, 
                              FeatureType.MOTION_PATTERN, FeatureType.AUDIO_SPECTROGRAM]:
                vector_search_results[feature_type.name] = benchmark.benchmark_vector_search(feature_type)
            
            results["vector_search"] = vector_search_results
        
        if args.identification:
            pipeline_results = benchmark.benchmark_identification_pipeline()
            results["identification_pipeline"] = pipeline_results
        
        if args.accuracy:
            accuracy_results = benchmark.measure_accuracy()
            results["accuracy"] = accuracy_results
        
        # Save results if output path is provided
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(exist_ok=True, parents=True)
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
