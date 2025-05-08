#!/usr/bin/env python3
"""
VidID Vector Database Demo Application

This is a simplified version of the VidID application that focuses on demonstrating
the vector database functionality.
"""

import os
import sys
import uuid
import logging
import asyncio
import numpy as np
import uvicorn
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add src directory to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import VidID modules
from src.core.vector_db_integration import VectorDBIntegration
from src.core.feature_extraction import FeatureType
from src.core.matching_engine import MatchingEngine, MatchingAlgorithm
from src.config.config import ConfigManager

# Create the FastAPI app
app = FastAPI(
    title="VidID Vector Database Demo",
    description="Demonstration of VidID's vector database functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Service dependencies ---

config_manager = ConfigManager()

def get_vector_db():
    """Get a vector database instance."""
    try:
        return VectorDBIntegration()
    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        raise HTTPException(status_code=500, detail="Vector database connection failed")

def get_matching_engine():
    """Get a matching engine instance."""
    try:
        return MatchingEngine({"match_threshold": 0.7})
    except Exception as e:
        logger.error(f"Error initializing matching engine: {e}")
        raise HTTPException(status_code=500, detail="Matching engine initialization failed")

# --- Models ---

class VectorInfo(BaseModel):
    dimension: int
    count: int
    feature_type: str

class VectorStats(BaseModel):
    total_vectors: int
    collections: Dict[str, VectorInfo]

class FeatureStoreRequest(BaseModel):
    vector: List[float]
    feature_type: str = "cnn_features"
    metadata: Optional[Dict[str, Any]] = None

class FeatureStoreResponse(BaseModel):
    feature_id: str
    video_id: str
    success: bool

class HealthResponse(BaseModel):
    status: str
    vector_db_type: str
    config: Dict[str, Any]
    collections: List[str]

# --- API Routes ---

@app.get("/", response_class=JSONResponse)
def read_root():
    """Root endpoint."""
    return {
        "app": "VidID Vector Database Demo",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/vector/stats",
            "/vector/store",
            "/vector/search"
        ]
    }

@app.get("/health", response_model=HealthResponse)
def health_check(vector_db: VectorDBIntegration = Depends(get_vector_db)):
    """Check the health of the application and the vector database connection."""
    try:
        # Get vector DB configuration
        vector_db_config = config_manager.get("vector_db", {})
        vector_db_type = vector_db_config.get("type", "unknown")
        
        # Get available collections
        collections = vector_db.vector_db_client.list_collections()
        
        return {
            "status": "healthy",
            "vector_db_type": vector_db_type,
            "config": vector_db_config,
            "collections": collections
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/vector/stats", response_model=VectorStats)
def get_vector_stats(vector_db: VectorDBIntegration = Depends(get_vector_db)):
    """Get statistics about the vectors stored in the database."""
    try:
        collections = vector_db.vector_db_client.list_collections()
        
        result = {
            "total_vectors": 0,
            "collections": {}
        }
        
        for collection in collections:
            try:
                count = vector_db.vector_db_client.get_collection_stats(collection)
                dimension = 0
                feature_type = "unknown"
                
                # Extract feature type from collection name
                if collection.startswith("vidid_"):
                    feature_type = collection[6:]
                
                # Get dimension based on feature type
                dims = {
                    "cnn_features": 2048,
                    "perceptual_hash": 64,
                    "motion_pattern": 256,
                    "audio_spectrogram": 512
                }
                dimension = dims.get(feature_type, 0)
                
                result["collections"][collection] = {
                    "dimension": dimension,
                    "count": count,
                    "feature_type": feature_type
                }
                
                result["total_vectors"] += count
            except Exception as e:
                logger.error(f"Error getting stats for collection {collection}: {e}")
                result["collections"][collection] = {
                    "dimension": 0,
                    "count": 0, 
                    "feature_type": "unknown",
                    "error": str(e)
                }
        
        return result
    except Exception as e:
        logger.error(f"Error getting vector statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting vector statistics: {str(e)}")

@app.post("/vector/store", response_model=FeatureStoreResponse)
def store_vector(
    request: FeatureStoreRequest,
    vector_db: VectorDBIntegration = Depends(get_vector_db)
):
    """Store a feature vector in the vector database."""
    try:
        # Convert feature type string to enum
        feature_types = {
            "cnn_features": FeatureType.CNN_FEATURES,
            "perceptual_hash": FeatureType.PERCEPTUAL_HASH,
            "motion_pattern": FeatureType.MOTION_PATTERN,
            "audio_spectrogram": FeatureType.AUDIO_SPECTROGRAM
        }
        
        feature_type = feature_types.get(request.feature_type)
        if not feature_type:
            raise HTTPException(status_code=400, detail=f"Unknown feature type: {request.feature_type}")
        
        # Generate a random video ID for testing
        video_id = f"demo_{uuid.uuid4().hex[:8]}"
        
        # Convert the vector to numpy array
        feature_vector = np.array(request.vector, dtype=np.float32)
        
        # Store the vector
        feature_id = vector_db.store_video_feature(
            video_id=video_id,
            feature_type=feature_type,
            feature_vector=feature_vector,
            metadata=request.metadata or {"source": "demo"}
        )
        
        return {
            "feature_id": feature_id,
            "video_id": video_id,
            "success": bool(feature_id)
        }
    except Exception as e:
        logger.error(f"Error storing vector: {e}")
        raise HTTPException(status_code=500, detail=f"Error storing vector: {str(e)}")

@app.post("/vector/search")
async def search_vector(
    request: FeatureStoreRequest,
    matching_engine = Depends(get_matching_engine),
    vector_db: VectorDBIntegration = Depends(get_vector_db)
):
    """Search for similar vectors in the vector database."""
    try:
        # Convert feature type string to enum
        feature_types = {
            "cnn_features": FeatureType.CNN_FEATURES,
            "perceptual_hash": FeatureType.PERCEPTUAL_HASH,
            "motion_pattern": FeatureType.MOTION_PATTERN,
            "audio_spectrogram": FeatureType.AUDIO_SPECTROGRAM
        }
        
        feature_type = feature_types.get(request.feature_type)
        if not feature_type:
            raise HTTPException(status_code=400, detail=f"Unknown feature type: {request.feature_type}")
        
        # Convert the vector to numpy array
        feature_vector = np.array(request.vector, dtype=np.float32)
        
        # Prepare the features dictionary for the matching engine
        features = {feature_type.value: feature_vector}
        
        # Prepare the video features structure with scenes
        video_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 0.0,
                    "features": features
                }
            ]
        }
        
        # Perform the search
        results = await matching_engine.match_video(
            video_features,
            algorithms=[MatchingAlgorithm.COSINE_SIMILARITY],
            top_k=5
        )
        
        # Convert results to JSON serializable format
        serialized_results = []
        for result in results:
            serialized_results.append({
                "content_id": result.content_id,
                "title": result.title,
                "confidence": result.confidence,
                "match_type": result.match_type,
                "timestamp": result.timestamp,
                "metadata": result.additional_metadata
            })
        
        return {
            "query": {
                "feature_type": request.feature_type,
                "vector_length": len(request.vector)
            },
            "results": serialized_results,
            "count": len(serialized_results)
        }
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching vectors: {str(e)}")

@app.post("/vector/generate-random")
def generate_random_vector(feature_type: str = "cnn_features"):
    """Generate a random vector for testing."""
    try:
        # Define dimensions for each feature type
        dims = {
            "cnn_features": 2048,
            "perceptual_hash": 64,
            "motion_pattern": 256,
            "audio_spectrogram": 512
        }
        
        dimension = dims.get(feature_type)
        if not dimension:
            raise HTTPException(status_code=400, detail=f"Unknown feature type: {feature_type}")
        
        # Generate a random vector
        if feature_type == "perceptual_hash":
            # Binary vector for perceptual hash
            vector = np.random.randint(0, 2, size=dimension).astype(np.float32)
        else:
            # Random vector for other feature types
            vector = np.random.rand(dimension).astype(np.float32)
        
        return {
            "feature_type": feature_type,
            "dimension": dimension,
            "vector": vector.tolist()
        }
    except Exception as e:
        logger.error(f"Error generating random vector: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating random vector: {str(e)}")

# --- Main function to run the app ---

def main():
    """Run the VidID Vector Database Demo Application."""
    print("=== VidID Vector Database Demo Application ===")
    print("Starting the API server...")
    
    # Load API configuration
    api_config = config_manager.get("api", {})
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8080)  # Use a different port
    debug = api_config.get("debug", True)
    
    # Run the server
    print(f"Starting server on {host}:{port}")
    uvicorn.run(
        app,  # Pass the app directly instead of as a string
        host=host,
        port=port,
        reload=debug
    )

if __name__ == "__main__":
    main()
