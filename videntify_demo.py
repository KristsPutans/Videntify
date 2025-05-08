#!/usr/bin/env python3
"""
Videntify Vector Database Demo

A simple demo application to showcase the vector database integration in the Videntify system.
"""

import os
import sys
import uuid
import json
import logging
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to path
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
    title="Videntify Vector Database Demo",
    description="Demonstration of Videntify's vector database functionality",
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

# --- API Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Root endpoint with a simple UI for interacting with the vector database."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Videntify Vector Database Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
            h1, h2 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .section { background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            .button { background: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
            .button:hover { background: #45a049; }
            pre { background: #f8f8f8; padding: 10px; overflow: auto; border-radius: 4px; }
            .result { margin-top: 20px; display: none; }
            label { display: block; margin-bottom: 5px; }
            input, select { margin-bottom: 10px; padding: 8px; width: 100%; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Videntify Vector Database Demo</h1>
            <p>This demo showcases the vector database integration in the Videntify system.</p>
            
            <div class="section">
                <h2>Vector Database Information</h2>
                <button id="check-health" class="button">Check Health</button>
                <div id="health-result" class="result"><pre></pre></div>
            </div>

            <div class="section">
                <h2>Vector Database Statistics</h2>
                <button id="check-stats" class="button">Get Statistics</button>
                <div id="stats-result" class="result"><pre></pre></div>
            </div>

            <div class="section">
                <h2>Store Random Vector</h2>
                <form id="store-form">
                    <label for="feature-type">Feature Type:</label>
                    <select id="feature-type" name="feature-type">
                        <option value="cnn_features">CNN Features</option>
                        <option value="perceptual_hash">Perceptual Hash</option>
                        <option value="motion_pattern">Motion Pattern</option>
                        <option value="audio_spectrogram">Audio Spectrogram</option>
                    </select>
                    <button type="submit" class="button">Generate and Store</button>
                </form>
                <div id="store-result" class="result"><pre></pre></div>
            </div>

            <div class="section">
                <h2>Search Similar Vectors</h2>
                <form id="search-form">
                    <label for="search-feature-type">Feature Type:</label>
                    <select id="search-feature-type" name="search-feature-type">
                        <option value="cnn_features">CNN Features</option>
                        <option value="perceptual_hash">Perceptual Hash</option>
                        <option value="motion_pattern">Motion Pattern</option>
                        <option value="audio_spectrogram">Audio Spectrogram</option>
                    </select>
                    <button type="submit" class="button">Generate and Search</button>
                </form>
                <div id="search-result" class="result"><pre></pre></div>
            </div>
        </div>

        <script>
            // Helper function to display JSON responses
            function displayJSON(elementId, data) {
                const element = document.getElementById(elementId);
                element.style.display = 'block';
                element.querySelector('pre').textContent = JSON.stringify(data, null, 2);
            }

            // Health check
            document.getElementById('check-health').addEventListener('click', async () => {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    displayJSON('health-result', data);
                } catch (error) {
                    displayJSON('health-result', { error: error.message });
                }
            });

            // Statistics
            document.getElementById('check-stats').addEventListener('click', async () => {
                try {
                    const response = await fetch('/vector/stats');
                    const data = await response.json();
                    displayJSON('stats-result', data);
                } catch (error) {
                    displayJSON('stats-result', { error: error.message });
                }
            });

            // Store random vector
            document.getElementById('store-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const featureType = document.getElementById('feature-type').value;
                try {
                    // First generate a random vector
                    const generateResponse = await fetch(`/vector/generate-random?feature_type=${featureType}`);
                    const vectorData = await generateResponse.json();
                    
                    // Then store it
                    const storeResponse = await fetch('/vector/store', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vector: vectorData.vector,
                            feature_type: featureType,
                            metadata: { source: 'demo-ui' }
                        })
                    });
                    
                    const storeResult = await storeResponse.json();
                    displayJSON('store-result', {
                        vector_info: vectorData,
                        store_result: storeResult
                    });
                } catch (error) {
                    displayJSON('store-result', { error: error.message });
                }
            });

            // Search similar vectors
            document.getElementById('search-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const featureType = document.getElementById('search-feature-type').value;
                try {
                    // First generate a random vector
                    const generateResponse = await fetch(`/vector/generate-random?feature_type=${featureType}`);
                    const vectorData = await generateResponse.json();
                    
                    // Then search for similar vectors
                    const searchResponse = await fetch('/vector/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vector: vectorData.vector,
                            feature_type: featureType
                        })
                    });
                    
                    const searchResult = await searchResponse.json();
                    displayJSON('search-result', {
                        vector_info: vectorData,
                        search_result: searchResult
                    });
                } catch (error) {
                    displayJSON('search-result', { error: error.message });
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
def health_check(vector_db: VectorDBIntegration = Depends(get_vector_db)):
    """Check the health of the application and the vector database connection."""
    try:
        # Get vector DB configuration
        vector_db_config = config_manager.get("vector_db", {})
        vector_db_type = vector_db_config.get("type", "unknown")
        
        # Make sure we're connected to the vector database
        if not hasattr(vector_db.vector_db_client, 'connected') or not vector_db.vector_db_client.connected:
            vector_db.vector_db_client.connect()
            
        # Get available collections - safely
        collections = []
        if hasattr(vector_db.vector_db_client, 'list_collections'):
            collections = vector_db.vector_db_client.list_collections()
        else:
            collections = ["collection_info_not_available"]
        
        # Create a minimal collection for demo purposes if none exist
        if len(collections) == 0 and hasattr(vector_db.vector_db_client, 'create_collection'):
            vector_db.vector_db_client.create_collection("vidid_cnn_features", 2048)
            collections = vector_db.vector_db_client.list_collections()
            
        return {
            "status": "healthy",
            "vector_db_type": vector_db_type,
            "config": vector_db_config,
            "collections": collections
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Return an error response instead of raising an exception
        return {
            "status": "error",
            "error": str(e),
            "vector_db_type": vector_db_config.get("type", "unknown") if 'vector_db_config' in locals() else "unknown",
            "config": vector_db_config if 'vector_db_config' in locals() else {}
        }

@app.get("/vector/stats")
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

@app.post("/vector/store")
def store_vector(
    request: dict,
    vector_db: VectorDBIntegration = Depends(get_vector_db)
):
    """Store a feature vector in the vector database."""
    try:
        # Extract data from request
        feature_type_str = request.get("feature_type", "cnn_features")
        vector_data = request.get("vector", [])
        metadata = request.get("metadata", {"source": "demo"})
        
        # Convert feature type string to enum
        feature_types = {
            "cnn_features": FeatureType.CNN_FEATURES,
            "perceptual_hash": FeatureType.PERCEPTUAL_HASH,
            "motion_pattern": FeatureType.MOTION_PATTERN,
            "audio_spectrogram": FeatureType.AUDIO_SPECTROGRAM
        }
        
        feature_type = feature_types.get(feature_type_str)
        if not feature_type:
            raise HTTPException(status_code=400, detail=f"Unknown feature type: {feature_type_str}")
        
        # Generate a random video ID for testing
        video_id = f"demo_{uuid.uuid4().hex[:8]}"
        
        # Convert the vector to numpy array
        feature_vector = np.array(vector_data, dtype=np.float32)
        
        # Store the vector
        feature_id = vector_db.store_video_feature(
            video_id=video_id,
            feature_type=feature_type,
            feature_vector=feature_vector,
            metadata=metadata
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
    request: dict,
    matching_engine = Depends(get_matching_engine),
    vector_db: VectorDBIntegration = Depends(get_vector_db)
):
    """Search for similar vectors in the vector database."""
    try:
        # Extract data from request
        feature_type_str = request.get("feature_type", "cnn_features")
        vector_data = request.get("vector", [])
        
        # Convert feature type string to enum
        feature_types = {
            "cnn_features": FeatureType.CNN_FEATURES,
            "perceptual_hash": FeatureType.PERCEPTUAL_HASH,
            "motion_pattern": FeatureType.MOTION_PATTERN,
            "audio_spectrogram": FeatureType.AUDIO_SPECTROGRAM
        }
        
        feature_type = feature_types.get(feature_type_str)
        if not feature_type:
            raise HTTPException(status_code=400, detail=f"Unknown feature type: {feature_type_str}")
        
        # Convert the vector to numpy array
        feature_vector = np.array(vector_data, dtype=np.float32)
        
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
                "feature_type": feature_type_str,
                "vector_length": len(vector_data)
            },
            "results": serialized_results,
            "count": len(serialized_results)
        }
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching vectors: {str(e)}")

@app.get("/vector/generate-random")
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

if __name__ == "__main__":
    import uvicorn
    print("=== Videntify Vector Database Demo ===\n")
    print("Starting the demo application on port 8095...")
    print("Open your browser at http://localhost:8095 to use the demo")
    
    uvicorn.run(app, host="0.0.0.0", port=8095)
