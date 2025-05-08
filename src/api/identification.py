"""Video Identification API

This module provides API endpoints for identifying videos in the VidID system.
"""

import logging
import uuid
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Query, Path, BackgroundTasks, Form, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.feature_extraction import FeatureType
from src.core.matching_engine import MatchingAlgorithm, MatchResult
from src.core.vector_db_integration import VectorDBIntegration
from src.feature_extraction import FeatureExtractionPipeline, FileSystemFeatureStorage, FeatureVector
from src.db.database import DatabaseManager
from src.db.models import Video, User, Query as QueryModel, QueryResult
from src.db.feature_storage import FeatureStorageManager
from src.utils.auth import get_current_user, get_optional_current_user
from src.utils.storage import ObjectStorage
from src.api.identification_vector_db import store_video_features_in_vector_db, prepare_matching_features

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/identify", tags=["identification"])

# Models for request/response validation
class IdentificationRequest(BaseModel):
    matching_algorithms: List[MatchingAlgorithm] = Field(
        default=[MatchingAlgorithm.ENSEMBLE],
        description="Matching algorithms to use"
    )
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum match confidence")
    save_query: bool = Field(default=True, description="Whether to save the query in the database")
    extract_features: List[FeatureType] = Field(
        default=[
            FeatureType.PERCEPTUAL_HASH,
            FeatureType.CNN_FEATURES,
            FeatureType.MOTION_PATTERN
        ],
        description="Features to extract"
    )


class IdentificationResultItem(BaseModel):
    video_id: str
    title: str
    confidence: float
    timestamp: Optional[float] = None
    thumbnail_url: Optional[str] = None
    source: Optional[str] = None
    match_type: str
    additional_info: Dict[str, Any] = {}


class IdentificationResponse(BaseModel):
    query_id: str
    results: List[IdentificationResultItem]
    processing_time_ms: float
    total_results: int
    status: str = "completed"


class AsyncIdentificationResponse(BaseModel):
    query_id: str
    status: str = "processing"
    eta_seconds: float = 0
    webhook_url: Optional[str] = None


class FrameIdentificationRequest(BaseModel):
    matching_algorithms: List[MatchingAlgorithm] = Field(
        default=[MatchingAlgorithm.COSINE_SIMILARITY],
        description="Matching algorithms to use"
    )
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum match confidence")
    save_query: bool = Field(default=True, description="Whether to save the query in the database")


class AudioIdentificationRequest(BaseModel):
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum match confidence")
    save_query: bool = Field(default=True, description="Whether to save the query in the database")


class QueryHistoryItem(BaseModel):
    query_id: str
    timestamp: datetime
    query_type: str
    result_count: int
    top_result: Optional[IdentificationResultItem] = None
    status: str


class QueryHistoryResponse(BaseModel):
    queries: List[QueryHistoryItem]
    total: int
    page: int
    page_size: int


# Dependencies
async def get_feature_pipeline():
    """Get the feature extraction pipeline."""
    config = {}
    features_dir = "/tmp/vidid/features"
    os.makedirs(features_dir, exist_ok=True)
    
    feature_storage = FileSystemFeatureStorage(features_dir)
    return FeatureExtractionPipeline(config=config, feature_storage=feature_storage)


async def get_vector_db_integration():
    """Get the vector database integration."""
    # Initialize the vector database integration
    return VectorDBIntegration()


async def get_feature_storage():
    """Get the feature storage manager."""
    # Initialize the feature storage manager
    return FeatureStorageManager()


async def get_matching_engine():
    """Get the matching engine."""
    # Initialize with vector database integration
    from src.core.matching_engine import MatchingEngine
    config = {"match_threshold": 0.7}
    return MatchingEngine(config)


async def get_db():
    """Get a database session."""
    # This would normally create a session from a SessionLocal factory
    return DatabaseManager().get_session()


async def get_object_storage():
    """Get the object storage client."""
    # This would normally be initialized from a configuration
    return ObjectStorage()


# Identification endpoints
@router.post("/video", response_model=IdentificationResponse)
async def identify_video(
    params: IdentificationRequest = Depends(),
    video_file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_current_user),
    feature_pipeline: FeatureExtractionPipeline = Depends(get_feature_pipeline),
    matching_engine = Depends(get_matching_engine),
    vector_db: VectorDBIntegration = Depends(get_vector_db_integration),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage)
):
    """
    Identify a video clip by uploading a file.
    """
    
    start_time = time.time()
    
    # Generate a unique ID for this query
    query_id = str(uuid.uuid4())
    
    # Save the uploaded file temporarily
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(await video_file.read())
        temp_path = temp_file.name
    
    try:
        # Create database record for the query
        if params.save_query and current_user:
            query_model = QueryModel(
                id=query_id,
                user_id=current_user.id,
                query_type="video",
                timestamp=datetime.utcnow(),
                parameters=params.dict(),
                status="processing"
            )
            db.add(query_model)
            db.commit()
        
        # Extract features from the video
        features = feature_pipeline.extract_features_from_video(temp_path)
        
        # Store features in vector database if required
        vector_features_stored = False
        if params.save_query and current_user:
            # Iterate through features and store in vector database
            for feature_name, feature_vector in features.items():
                feat_type = None
                if "visual_cnn" in feature_name:
                    feat_type = FeatureType.CNN_FEATURES
                elif "visual_phash" in feature_name:
                    feat_type = FeatureType.PERCEPTUAL_HASH
                elif "visual_motion" in feature_name:
                    feat_type = FeatureType.MOTION_PATTERN
                elif "audio_fingerprint" in feature_name:
                    feat_type = FeatureType.AUDIO_SPECTROGRAM
                
                if feat_type:
                    try:
                        # Store feature vector in the vector database
                        feature_id = vector_db.store_video_feature(
                            video_id=query_id,
                            feature_type=feat_type,
                            feature_vector=feature_vector.vector,
                            metadata={"is_query": True, "query_type": "video"}
                        )
                        if feature_id:
                            vector_features_stored = True
                            logger.debug(f"Stored {feature_name} in vector database with ID {feature_id}")
                    except Exception as e:
                        logger.error(f"Error storing {feature_name} in vector database: {e}")
        
# Convert extracted features to format needed by matching engine
        matching_features = {}
        for feature_name, feature_vector in features.items():
            if "visual_cnn" in feature_name:
                matching_features[FeatureType.CNN_FEATURES.value] = feature_vector.vector
            elif "visual_phash" in feature_name:
                matching_features[FeatureType.PERCEPTUAL_HASH.value] = feature_vector.vector
            elif "visual_motion" in feature_name:
                matching_features[FeatureType.MOTION_PATTERN.value] = feature_vector.vector
            elif "audio_fingerprint" in feature_name:
                matching_features[FeatureType.AUDIO_SPECTROGRAM.value] = feature_vector.vector
        
        # Perform matching
        # Create proper video features structure with scenes
        video_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 10.0,  # Default duration estimate
                    "features": matching_features
                }
            ]
        }
        
        # Call matching engine with correct parameters
        match_results = await matching_engine.match_video(
            video_features,
            algorithms=[MatchingAlgorithm(algo) for algo in params.algorithms],
            top_k=params.max_results
        )
        
        # Calculate processing time
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # in milliseconds
        
        # Create response items
        result_items = []
        for match in match_results:
            # Get video details from the database
            video = db.query(Video).filter(Video.id == match.content_id).first()
            thumbnail_url = None
            title = match.title
            source = None
            
            if video:
                thumbnail_url = f"/api/videos/thumbnail/{video.id}"
                title = video.title
                source = video.source
            
            result_items.append(IdentificationResultItem(
                video_id=match.content_id,
                title=title,
                confidence=match.confidence,
                timestamp=match.timestamp,
                thumbnail_url=thumbnail_url,
                source=source,
                match_type=match.match_type,
                additional_info=match.additional_metadata
            ))
        
        # Update query record with results
        if params.save_query and current_user:
            query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
            if query_model:
                query_model.status = "completed"
                query_model.processing_time = processing_time
                db.commit()
                
                # Save results
                for i, result in enumerate(result_items):
                    query_result = QueryResult(
                        query_id=query_id,
                        content_id=result.video_id,
                        rank=i + 1,
                        confidence=result.confidence,
                        match_type=result.match_type
                    )
                    db.add(query_result)
                db.commit()
        
        # Save the query clip if there were successful matches
        if result_items and params.save_query and current_user:
            storage_path = f"queries/{query_id}.mp4"
            storage.upload_file(temp_path, storage_path)
        
        return IdentificationResponse(
            query_id=query_id,
            results=result_items,
            processing_time_ms=processing_time,
            total_results=len(result_items),
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Error identifying video: {str(e)}")
        
        # Update query status
        if params.save_query and current_user:
            query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
            if query_model:
                query_model.status = "error"
                query_model.error_message = str(e)
                db.commit()
        
        raise HTTPException(status_code=500, detail=f"Error identifying video: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/video/async", response_model=AsyncIdentificationResponse)
async def identify_video_async(
    background_tasks: BackgroundTasks,
    params: IdentificationRequest = Depends(),
    video_file: UploadFile = File(...),
    webhook_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    vector_db: VectorDBIntegration = Depends(get_vector_db_integration),
    db: Session = Depends(get_db)
):
    """
Start asynchronous video identification.
    """
    # Generate a unique ID for this query
    query_id = str(uuid.uuid4())
    
    # Save the uploaded file temporarily
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(await video_file.read())
        temp_path = temp_file.name
    
    # Create database record for the query
    query_model = QueryModel(
        id=query_id,
        user_id=current_user.id,
        query_type="video_async",
        timestamp=datetime.utcnow(),
        parameters={**params.dict(), "webhook_url": webhook_url},
        status="queued"
    )
    db.add(query_model)
    db.commit()
    
    # Add task to background queue
    background_tasks.add_task(
        process_identification_async,
        query_id=query_id,
        temp_path=temp_path,
        params=params,
        webhook_url=webhook_url
    )
    
    return AsyncIdentificationResponse(
        query_id=query_id,
        status="processing",
        eta_seconds=10.0,  # Estimated time, adjust based on average processing time
        webhook_url=webhook_url
    )


async def process_identification_async(
    query_id: str,
    temp_path: str,
    params: IdentificationRequest,
    webhook_url: Optional[str] = None,
    vector_db: VectorDBIntegration = None
):
    """
Process asynchronous identification in the background.
    """
    try:
        # Get services
        db = router.app.state.db_manager.get_db_session()
        storage = router.app.state.object_storage
        feature_pipeline = await get_feature_pipeline()
        matching_engine = router.app.state.matching_engine
        
        # Update query status
        query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
        if not query_model:
            logger.error(f"Query not found: {query_id}")
            return
        
        query_model.status = "processing"
        db.commit()
        
        start_time = time.time()
        
        # Extract features from the video
        features = feature_pipeline.extract_features_from_video(temp_path)
        
        # Store features in vector database if required
        vector_features_stored = False
        if params.save_query and current_user:
            # Iterate through features and store in vector database
            for feature_name, feature_vector in features.items():
                feat_type = None
                if "visual_cnn" in feature_name:
                    feat_type = FeatureType.CNN_FEATURES
                elif "visual_phash" in feature_name:
                    feat_type = FeatureType.PERCEPTUAL_HASH
                elif "visual_motion" in feature_name:
                    feat_type = FeatureType.MOTION_PATTERN
                elif "audio_fingerprint" in feature_name:
                    feat_type = FeatureType.AUDIO_SPECTROGRAM
                
                if feat_type:
                    try:
                        # Store feature vector in the vector database
                        feature_id = vector_db.store_video_feature(
                            video_id=query_id,
                            feature_type=feat_type,
                            feature_vector=feature_vector.vector,
                            metadata={"is_query": True, "query_type": "video"}
                        )
                        if feature_id:
                            vector_features_stored = True
                            logger.debug(f"Stored {feature_name} in vector database with ID {feature_id}")
                    except Exception as e:
                        logger.error(f"Error storing {feature_name} in vector database: {e}")
        
# Convert extracted features to format needed by matching engine
        matching_features = {}
        for feature_name, feature_vector in features.items():
            if "visual_cnn" in feature_name:
                matching_features[FeatureType.CNN_FEATURES.value] = feature_vector.vector
            elif "visual_phash" in feature_name:
                matching_features[FeatureType.PERCEPTUAL_HASH.value] = feature_vector.vector
            elif "visual_motion" in feature_name:
                matching_features[FeatureType.MOTION_PATTERN.value] = feature_vector.vector
            elif "audio_fingerprint" in feature_name:
                matching_features[FeatureType.AUDIO_SPECTROGRAM.value] = feature_vector.vector
        
        # Perform matching
        # Create proper video features structure with scenes
        video_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 10.0,  # Default duration estimate
                    "features": matching_features
                }
            ]
        }
        
        # Call matching engine with correct parameters
        match_results = await matching_engine.match_video(
            video_features,
            algorithms=[MatchingAlgorithm(algo) for algo in params.algorithms],
            top_k=params.max_results
        )
        
        # Calculate processing time
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # in milliseconds
        
        # Create response items
        result_items = []
        for match in match_results:
            # Get video details from the database
            video = db.query(Video).filter(Video.id == match.content_id).first()
            thumbnail_url = None
            title = match.title
            source = None
            
            if video:
                thumbnail_url = f"/api/videos/thumbnail/{video.id}"
                title = video.title
                source = video.source
            
            result_items.append({
                "video_id": match.content_id,
                "title": title,
                "confidence": match.confidence,
                "timestamp": match.timestamp,
                "thumbnail_url": thumbnail_url,
                "source": source,
                "match_type": match.match_type,
                "additional_info": match.additional_metadata
            })
        
        # Update query record with results
        query_model.status = "completed"
        query_model.processing_time = processing_time
        query_model.result_count = len(result_items)
        db.commit()
        
        # Save results
        for i, result in enumerate(result_items):
            query_result = QueryResult(
                query_id=query_id,
                content_id=result["video_id"],
                rank=i + 1,
                confidence=result["confidence"],
                match_type=result["match_type"]
            )
            db.add(query_result)
        db.commit()
        
        # Save the query clip if there were successful matches
        if result_items:
            storage_path = f"queries/{query_id}.mp4"
            storage.upload_file(temp_path, storage_path)
        
        # Call webhook if provided
        if webhook_url:
            import requests
            webhook_data = {
                "query_id": query_id,
                "status": "completed",
                "processing_time_ms": processing_time,
                "total_results": len(result_items),
                "result_summary": [{
                    "video_id": r["video_id"],
                    "confidence": r["confidence"],
                    "match_type": r["match_type"]
                } for r in result_items[:3]]  # Send summary of top 3 results
            }
            try:
                requests.post(webhook_url, json=webhook_data, timeout=5)
            except Exception as e:
                logger.error(f"Error calling webhook: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in async identification: {str(e)}")
        
        # Update query status
        db = router.app.state.db_manager.get_db_session()
        query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
        if query_model:
            query_model.status = "error"
            query_model.error_message = str(e)
            db.commit()
            
        # Call webhook with error if provided
        if webhook_url:
            import requests
            webhook_data = {
                "query_id": query_id,
                "status": "error",
                "error": str(e)
            }
            try:
                requests.post(webhook_url, json=webhook_data, timeout=5)
            except Exception as webhook_err:
                logger.error(f"Error calling webhook: {str(webhook_err)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/frame", response_model=IdentificationResponse)
async def identify_frame(
    params: FrameIdentificationRequest = Depends(),
    frame_file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_current_user),
    feature_pipeline: FeatureExtractionPipeline = Depends(get_feature_pipeline),
    matching_engine = Depends(get_matching_engine),
    vector_db: VectorDBIntegration = Depends(get_vector_db_integration),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage)
):
    """
Identify a single video frame.
    """
    start_time = time.time()
    
    # Generate a unique ID for this query
    query_id = str(uuid.uuid4())
    
    # Save the uploaded file temporarily
    with NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(await frame_file.read())
        temp_path = temp_file.name
    
    try:
        # Create database record for the query
        if params.save_query and current_user:
            query_model = QueryModel(
                id=query_id,
                user_id=current_user.id,
                query_type="frame",
                timestamp=datetime.utcnow(),
                parameters=params.dict(),
                status="processing"
            )
            db.add(query_model)
            db.commit()
        
        # Extract features from the frame
        features = feature_pipeline.extract_features_from_image(temp_path)
        
        # Store features in vector database if required
        vector_features_stored = False
        if params.save_query and current_user:
            # Use the helper function to store features in vector database
            vector_features_stored = store_video_features_in_vector_db(
                vector_db=vector_db,
                query_id=query_id,
                features=features,
                save_query=params.save_query,
                query_type="frame"
            )
        
        # Convert features to the format expected by the matching engine
        matching_features = {}
        # Convert features to the format expected by the matching engine
        matching_features = prepare_matching_features(features)
        
        # Prepare a proper frame features structure with a single scene
        frame_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 0.0,  # Single frame has no duration
                    "features": matching_features
                }
            ]
        }
        
        # Perform matching using the video matching function
        match_results = await matching_engine.match_video(
            frame_features,
            algorithms=[MatchingAlgorithm(algo) for algo in params.algorithms],
            top_k=params.max_results
        )
        
        # Calculate processing time
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # in milliseconds
        
        # Create response items
        result_items = []
        for match in match_results:
            # Get video details from the database
            video = db.query(Video).filter(Video.id == match.content_id).first()
            thumbnail_url = None
            title = match.title
            source = None
            
            if video:
                thumbnail_url = f"/api/videos/thumbnail/{video.id}"
                title = video.title
                source = video.source
            
            result_items.append(IdentificationResultItem(
                video_id=match.content_id,
                title=title,
                confidence=match.confidence,
                timestamp=match.timestamp,
                thumbnail_url=thumbnail_url,
                source=source,
                match_type=match.match_type,
                additional_info=match.additional_metadata
            ))
        
        # Update query record with results
        if params.save_query and current_user:
            query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
            if query_model:
                query_model.status = "completed"
                query_model.processing_time = processing_time
                db.commit()
                
                # Save results
                for i, result in enumerate(result_items):
                    query_result = QueryResult(
                        query_id=query_id,
                        content_id=result.video_id,
                        rank=i + 1,
                        confidence=result.confidence,
                        match_type=result.match_type
                    )
                    db.add(query_result)
                db.commit()
        
        # Save the query frame if there were successful matches
        if result_items and params.save_query and current_user:
            storage_path = f"queries/{query_id}.jpg"
            storage.upload_file(temp_path, storage_path)
        
        return IdentificationResponse(
            query_id=query_id,
            results=result_items,
            processing_time_ms=processing_time,
            total_results=len(result_items),
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Error identifying frame: {str(e)}")
        
        # Update query status
        if params.save_query and current_user:
            query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
            if query_model:
                query_model.status = "error"
                query_model.error_message = str(e)
                db.commit()
        
        raise HTTPException(status_code=500, detail=f"Error identifying frame: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/audio", response_model=IdentificationResponse)
async def identify_audio(
    params: AudioIdentificationRequest = Depends(),
    audio_file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_current_user),
    feature_pipeline: FeatureExtractionPipeline = Depends(get_feature_pipeline),
    matching_engine = Depends(get_matching_engine),
    vector_db: VectorDBIntegration = Depends(get_vector_db_integration),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage)
):
    """
Identify audio content.
    """
    # Generate a query ID
    query_id = str(uuid.uuid4())
    logger.info(f"Processing audio identification request {query_id}")
    
    # Save the query if requested
    if params.save_query and current_user:
        query_model = QueryModel(
            id=query_id,
            user_id=current_user.id,
            type="audio",
            status="processing",
            created_at=datetime.now(),
            algorithms=params.algorithms,
            threshold=params.threshold,
        )
        db.add(query_model)
        db.commit()
    
    # Save the audio file to a temporary location
    temp_path = f"/tmp/vidid_temp_audio_{query_id}{os.path.splitext(audio_file.filename)[1]}"
    try:
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
            
        # Extract features
        features = feature_pipeline.extract_features_from_audio(temp_path)
        
        # Store features in vector database if save_query is enabled
        if params.save_query and current_user:
            store_video_features_in_vector_db(
                vector_db=vector_db,
                query_id=query_id,
                features=features,
                save_query=params.save_query,
                query_type="audio"
            )
        
        # Convert features to the format expected by the matching engine
        matching_features = prepare_matching_features(features)
        
        # Prepare a proper audio features structure
        audio_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 0.0,  # Will be calculated during processing
                    "features": matching_features
                }
            ]
        }
        
        # Match against the database
        results = await matching_engine.match_video(
            audio_features,
            algorithms=[MatchingAlgorithm(algo) for algo in params.algorithms],
            top_k=params.max_results
        )
        
        # Filter results based on threshold
        filtered_results = [r for r in results if r.confidence >= params.threshold]
        
        # Save results if requested
        if params.save_query and current_user:
            # Update query status
            query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
            if query_model:
                query_model.status = "completed"
                query_model.completed_at = datetime.now()
                
                # Save results
                for idx, result in enumerate(filtered_results):
                    query_result = QueryResult(
                        query_id=query_id,
                        content_id=result.content_id,
                        confidence=result.confidence,
                        match_type=result.match_type,
                        rank=idx + 1,
                        metadata=json.dumps(result.additional_metadata) if result.additional_metadata else None
                    )
                    db.add(query_result)
                
                db.commit()
        
        # Return response
        return {
            "query_id": query_id,
            "results": filtered_results,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error identifying audio: {e}")
        
        # Update query status
        if params.save_query and current_user:
            query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
            if query_model:
                query_model.status = "error"
                query_model.error_message = str(e)
                db.commit()
        
        raise HTTPException(status_code=500, detail=f"Error identifying audio: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/query/{query_id}", response_model=IdentificationResponse)
async def get_query_results(
    query_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
Get the results of a previous identification query.
    """
    # Get query from database
    query_model = db.query(QueryModel).filter(QueryModel.id == query_id).first()
    if not query_model:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Check permissions
    if query_model.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to access this query")
    
    # Get results
    results = db.query(QueryResult).filter(QueryResult.query_id == query_id).order_by(QueryResult.rank).all()
    
    # Build response items
    result_items = []
    for result in results:
        # Get video details
        video = db.query(Video).filter(Video.id == result.content_id).first()
        thumbnail_url = None
        title = "Unknown"
        source = None
        
        if video:
            thumbnail_url = f"/api/videos/thumbnail/{video.id}"
            title = video.title
            source = video.source
        
        result_items.append(IdentificationResultItem(
            video_id=result.content_id,
            title=title,
            confidence=result.confidence,
            timestamp=result.timestamp,
            thumbnail_url=thumbnail_url,
            source=source,
            match_type=result.match_type,
            additional_info=result.additional_data or {}
        ))
    
    return IdentificationResponse(
        query_id=query_id,
        results=result_items,
        processing_time_ms=query_model.processing_time or 0,
        total_results=len(result_items),
        status=query_model.status
    )


@router.get("/history", response_model=QueryHistoryResponse)
async def get_query_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
Get the user's query history.
    """
    # Build query
    query = db.query(QueryModel).filter(QueryModel.user_id == current_user.id)
    
    # Apply filters
    if query_type:
        query = query.filter(QueryModel.query_type == query_type)
    
    # Sort by timestamp (most recent first)
    query = query.order_by(QueryModel.timestamp.desc())
    
    # Count total
    total = query.count()
    
    # Paginate
    queries = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response items
    history_items = []
    for query_model in queries:
        # Get the top result
        top_result = db.query(QueryResult).filter(
            QueryResult.query_id == query_model.id,
            QueryResult.rank == 1
        ).first()
        
        top_result_item = None
        if top_result:
            # Get video details
            video = db.query(Video).filter(Video.id == top_result.content_id).first()
            thumbnail_url = None
            title = "Unknown"
            source = None
            
            if video:
                thumbnail_url = f"/api/videos/thumbnail/{video.id}"
                title = video.title
                source = video.source
            
            top_result_item = IdentificationResultItem(
                video_id=top_result.content_id,
                title=title,
                confidence=top_result.confidence,
                timestamp=top_result.timestamp,
                thumbnail_url=thumbnail_url,
                source=source,
                match_type=top_result.match_type,
                additional_info=top_result.additional_data or {}
            )
        
        history_items.append(QueryHistoryItem(
            query_id=query_model.id,
            timestamp=query_model.timestamp,
            query_type=query_model.query_type,
            result_count=query_model.result_count or 0,
            top_result=top_result_item,
            status=query_model.status
        ))
    
    return QueryHistoryResponse(
        queries=history_items,
        total=total,
        page=page,
        page_size=page_size
    )
