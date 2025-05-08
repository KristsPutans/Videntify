"""Video Management API

This module provides API endpoints for managing videos in the VidID system.
"""

import logging
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.feature_extraction import FeatureType
from src.feature_extraction import FeatureExtractionPipeline, FileSystemFeatureStorage
from src.db.database import DatabaseManager
from src.db.models import Video, User
from src.utils.auth import get_current_user
from src.utils.storage import ObjectStorage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/videos", tags=["videos"])

# Models for request/response validation
class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    content_type: str
    size_bytes: int
    duration: Optional[float] = None
    status: str
    feature_extraction_status: str
    upload_time: datetime
    features_extracted: List[str] = []


class VideoMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []
    custom_metadata: Dict[str, Any] = {}


class VideoUpdateRequest(BaseModel):
    metadata: Optional[VideoMetadata] = None
    is_public: Optional[bool] = None
    status: Optional[str] = None


class VideoResponse(BaseModel):
    video_id: str
    filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    status: str
    is_public: bool
    upload_time: datetime
    last_modified: datetime
    size_bytes: int
    features_extracted: List[str] = []
    custom_metadata: Dict[str, Any] = {}


class VideoListResponse(BaseModel):
    videos: List[VideoResponse]
    total: int
    page: int
    page_size: int


class FeatureExtractionRequest(BaseModel):
    feature_types: List[FeatureType] = [
        FeatureType.PERCEPTUAL_HASH,
        FeatureType.CNN_FEATURES,
        FeatureType.MOTION_PATTERN
    ]
    force_reextract: bool = False


class FeatureExtractionResponse(BaseModel):
    video_id: str
    features_extracted: List[str]
    status: str
    message: str


class SimilaritySearchRequest(BaseModel):
    video_id: Optional[str] = None
    feature_types: List[FeatureType] = [FeatureType.CNN_FEATURES]
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_results: int = Field(default=10, ge=1, le=100)


class SimilarityResult(BaseModel):
    video_id: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    similarity_score: float
    matching_features: List[str]


class SimilaritySearchResponse(BaseModel):
    results: List[SimilarityResult]
    total_results: int
    query_video_id: Optional[str] = None
    threshold: float


# Dependencies
async def get_feature_pipeline(db_manager=Depends(lambda: router.app.state.db_manager)):
    """
Get the feature extraction pipeline.
    """
    features_dir = router.app.state.config.get("features_dir", "/tmp/vidid/features")
    os.makedirs(features_dir, exist_ok=True)
    
    feature_storage = FileSystemFeatureStorage(features_dir)
    return FeatureExtractionPipeline(config=router.app.state.config, feature_storage=feature_storage)


async def get_object_storage():
    """
Get the object storage client.
    """
    return router.app.state.object_storage


async def get_db(db_manager=Depends(lambda: router.app.state.db_manager)):
    """
Get a database session.
    """
    return db_manager.get_db_session()


# Video upload and download endpoints
@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    tags: List[str] = Query([]),
    current_user: User = Depends(get_current_user),
    storage: ObjectStorage = Depends(get_object_storage),
    feature_pipeline: FeatureExtractionPipeline = Depends(get_feature_pipeline),
    db: Session = Depends(get_db)
):
    """
Upload a video file and start processing it.
    """
    # Generate a unique ID for the video
    video_id = str(uuid.uuid4())
    
    # Save the uploaded file temporarily
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(await video_file.read())
        temp_path = temp_file.name
    
    try:
        # Extract basic metadata
        import cv2
        cap = cv2.VideoCapture(temp_path)
        file_size = os.path.getsize(temp_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        # Upload to object storage
        storage_path = f"videos/{video_id}/{video_file.filename}"
        storage.upload_file(temp_path, storage_path)
        
        # Generate a thumbnail
        thumbnail_path = f"/tmp/{video_id}_thumbnail.jpg"
        feature_pipeline.create_thumbnail(temp_path, thumbnail_path, method="mosaic")
        
        # Upload thumbnail
        thumbnail_storage_path = f"thumbnails/{video_id}.jpg"
        storage.upload_file(thumbnail_path, thumbnail_storage_path)
        
        # Create database record
        video = Video(
            id=video_id,
            filename=video_file.filename,
            original_filename=video_file.filename,
            content_type=video_file.content_type,
            size_bytes=file_size,
            duration=duration,
            user_id=current_user.id,
            title=title or video_file.filename,
            description=description,
            tags=tags,
            storage_path=storage_path,
            thumbnail_path=thumbnail_storage_path,
            status="uploaded",
            feature_extraction_status="pending",
            is_public=False,
            upload_time=datetime.utcnow(),
            last_modified=datetime.utcnow()
        )
        
        db.add(video)
        db.commit()
        
        # Start feature extraction in the background
        background_tasks.add_task(
            extract_features_background,
            video_id=video_id,
            temp_path=temp_path,
            feature_pipeline=feature_pipeline,
            db=db
        )
        
        # Return response
        return VideoUploadResponse(
            video_id=video_id,
            filename=video_file.filename,
            content_type=video_file.content_type,
            size_bytes=file_size,
            duration=duration,
            status="uploaded",
            feature_extraction_status="pending",
            upload_time=video.upload_time,
            features_extracted=[]
        )
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        if os.path.exists(thumbnail_path):
            os.unlink(thumbnail_path)


async def extract_features_background(
    video_id: str,
    temp_path: str,
    feature_pipeline: FeatureExtractionPipeline,
    db: Session
):
    """
Extract features from a video in the background.
    """
    try:
        # Update status
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Video not found: {video_id}")
            return
        
        video.feature_extraction_status = "processing"
        db.commit()
        
        # Extract features
        features = feature_pipeline.extract_features_from_video(
            temp_path, video_id=video_id
        )
        
        # Update status
        video.feature_extraction_status = "completed"
        video.features_extracted = list(features.keys())
        video.status = "ready"
        db.commit()
        
        logger.info(f"Feature extraction completed for video {video_id}")
        
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        if db:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.feature_extraction_status = "failed"
                video.status = "error"
                db.commit()


@router.get("/stream/{video_id}")
async def stream_video(
    video_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    storage: ObjectStorage = Depends(get_object_storage),
    db: Session = Depends(get_db)
):
    """
Stream a video file.
    """
    # Get video from database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check permission
    if video.user_id != current_user.id and not video.is_public and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to access this video")
    
    # Get presigned URL for the video
    presigned_url = storage.get_presigned_url(video.storage_path, expires_in=3600)
    
    # Return a redirect to the presigned URL
    return {"stream_url": presigned_url}


@router.get("/thumbnail/{video_id}")
async def get_thumbnail(
    video_id: str = Path(...),
    current_user: Optional[User] = Depends(get_current_user),
    storage: ObjectStorage = Depends(get_object_storage),
    db: Session = Depends(get_db)
):
    """
Get the thumbnail for a video.
    """
    # Get video from database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check permission for private videos
    if (current_user is None or (video.user_id != current_user.id and not current_user.is_admin)) and not video.is_public:
        raise HTTPException(status_code=403, detail="You don't have permission to access this video")
    
    # Get presigned URL for the thumbnail
    presigned_url = storage.get_presigned_url(video.thumbnail_path, expires_in=3600)
    
    # Return a redirect to the presigned URL
    return {"thumbnail_url": presigned_url}


# Video management endpoints
@router.get("/", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tag: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    title_search: Optional[str] = Query(None),
    sort_by: str = Query("upload_time"),
    sort_order: str = Query("desc")
):
    """
List videos for the current user.
    """
    # Build query
    query = db.query(Video)
    
    # Filter by user unless admin
    if not current_user.is_admin:
        query = query.filter((Video.user_id == current_user.id) | (Video.is_public == True))
    
    # Apply filters
    if tag:
        query = query.filter(Video.tags.contains([tag]))
    if status:
        query = query.filter(Video.status == status)
    if title_search:
        query = query.filter(Video.title.ilike(f"%{title_search}%"))
    
    # Apply sorting
    if sort_order.lower() == "asc":
        query = query.order_by(getattr(Video, sort_by))
    else:
        query = query.order_by(getattr(Video, sort_by).desc())
    
    # Count total
    total = query.count()
    
    # Paginate
    videos = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response
    return VideoListResponse(
        videos=[
            VideoResponse(
                video_id=video.id,
                filename=video.filename,
                title=video.title,
                description=video.description,
                tags=video.tags,
                duration=video.duration,
                thumbnail_url=f"/api/videos/thumbnail/{video.id}",
                status=video.status,
                is_public=video.is_public,
                upload_time=video.upload_time,
                last_modified=video.last_modified,
                size_bytes=video.size_bytes,
                features_extracted=video.features_extracted or [],
                custom_metadata=video.custom_metadata or {}
            ) for video in videos
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
Get video details.
    """
    # Get video from database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check permission
    if video.user_id != current_user.id and not video.is_public and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to access this video")
    
    # Return response
    return VideoResponse(
        video_id=video.id,
        filename=video.filename,
        title=video.title,
        description=video.description,
        tags=video.tags,
        duration=video.duration,
        thumbnail_url=f"/api/videos/thumbnail/{video.id}",
        status=video.status,
        is_public=video.is_public,
        upload_time=video.upload_time,
        last_modified=video.last_modified,
        size_bytes=video.size_bytes,
        features_extracted=video.features_extracted or [],
        custom_metadata=video.custom_metadata or {}
    )


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str = Path(...),
    update_data: VideoUpdateRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
Update video metadata.
    """
    # Get video from database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check permission
    if video.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to update this video")
    
    # Update fields
    if update_data.metadata:
        metadata = update_data.metadata
        if metadata.title is not None:
            video.title = metadata.title
        if metadata.description is not None:
            video.description = metadata.description
        if metadata.tags:
            video.tags = metadata.tags
        if metadata.source is not None:
            video.source = metadata.source
        if metadata.custom_metadata:
            video.custom_metadata = metadata.custom_metadata
    
    if update_data.is_public is not None:
        video.is_public = update_data.is_public
    
    if update_data.status is not None and current_user.is_admin:
        video.status = update_data.status
    
    video.last_modified = datetime.utcnow()
    db.commit()
    
    # Return updated video
    return VideoResponse(
        video_id=video.id,
        filename=video.filename,
        title=video.title,
        description=video.description,
        tags=video.tags,
        duration=video.duration,
        thumbnail_url=f"/api/videos/thumbnail/{video.id}",
        status=video.status,
        is_public=video.is_public,
        upload_time=video.upload_time,
        last_modified=video.last_modified,
        size_bytes=video.size_bytes,
        features_extracted=video.features_extracted or [],
        custom_metadata=video.custom_metadata or {}
    )


@router.delete("/{video_id}")
async def delete_video(
    video_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    storage: ObjectStorage = Depends(get_object_storage),
    db: Session = Depends(get_db)
):
    """
Delete a video.
    """
    # Get video from database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check permission
    if video.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this video")
    
    # Delete from storage
    storage.delete_file(video.storage_path)
    if video.thumbnail_path:
        storage.delete_file(video.thumbnail_path)
    
    # Delete from database
    db.delete(video)
    db.commit()
    
    return {"message": "Video deleted successfully"}


# Feature extraction endpoints
@router.post("/{video_id}/extract-features", response_model=FeatureExtractionResponse)
async def extract_features(
    background_tasks: BackgroundTasks,
    video_id: str = Path(...),
    request: FeatureExtractionRequest = Depends(),
    current_user: User = Depends(get_current_user),
    storage: ObjectStorage = Depends(get_object_storage),
    feature_pipeline: FeatureExtractionPipeline = Depends(get_feature_pipeline),
    db: Session = Depends(get_db)
):
    """
Extract features from a video.
    """
    # Get video from database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check permission
    if video.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to process this video")
    
    # Check if features are already being extracted
    if video.feature_extraction_status == "processing" and not request.force_reextract:
        return FeatureExtractionResponse(
            video_id=video_id,
            features_extracted=video.features_extracted or [],
            status="processing",
            message="Feature extraction is already in progress"
        )
    
    # Download video to temporary file
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        storage.download_file(video.storage_path, temp_file.name)
        temp_path = temp_file.name
    
    # Update status
    video.feature_extraction_status = "processing"
    db.commit()
    
    # Start feature extraction in the background
    background_tasks.add_task(
        extract_features_background,
        video_id=video_id,
        temp_path=temp_path,
        feature_pipeline=feature_pipeline,
        db=db
    )
    
    return FeatureExtractionResponse(
        video_id=video_id,
        features_extracted=video.features_extracted or [],
        status="processing",
        message="Feature extraction started"
    )


# Similarity search endpoint
@router.post("/search/similarity", response_model=SimilaritySearchResponse)
async def search_similar_videos(
    request: SimilaritySearchRequest,
    current_user: User = Depends(get_current_user),
    storage: ObjectStorage = Depends(get_object_storage),
    feature_pipeline: FeatureExtractionPipeline = Depends(get_feature_pipeline),
    db: Session = Depends(get_db)
):
    """
Search for videos similar to a given video.
    """
    if not request.video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    
    # Get query video from database
    query_video = db.query(Video).filter(Video.id == request.video_id).first()
    if not query_video:
        raise HTTPException(status_code=404, detail="Query video not found")
    
    # Check permission for query video
    if query_video.user_id != current_user.id and not query_video.is_public and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to use this video as a query")
    
    # Get features for the query video
    feature_storage = feature_pipeline.feature_storage
    query_features = feature_storage.retrieve_features(request.video_id)
    
    # Check if requested feature types are available
    available_feature_types = []
    for feature_type in request.feature_types:
        feature_name = f"visual_{feature_type.value}"
        if feature_name in query_features:
            available_feature_types.append(feature_name)
    
    if not available_feature_types:
        raise HTTPException(
            status_code=400, 
            detail=f"None of the requested feature types are available for this video"
        )
    
    # Search for similar videos using each feature type
    results = []
    for feature_type in available_feature_types:
        feature_vector = query_features[feature_type]
        similar_items = feature_storage.search_similar(
            feature_vector,
            feature_type,
            limit=request.max_results,
            threshold=request.threshold
        )
        
        # Add to results
        for item in similar_items:
            # Skip the query video itself
            if item['id'] == request.video_id:
                continue
                
            # Get video details
            video = db.query(Video).filter(Video.id == item['id']).first()
            if not video:
                continue
                
            # Check if user has permission to see this video
            if video.user_id != current_user.id and not video.is_public and not current_user.is_admin:
                continue
                
            # Add to results
            results.append({
                'video_id': video.id,
                'title': video.title,
                'similarity_score': item['similarity'],
                'thumbnail_url': f"/api/videos/thumbnail/{video.id}",
                'matching_features': [feature_type]
            })
    
    # Aggregate results (if a video appears multiple times, keep the highest score)
    aggregated = {}
    for result in results:
        video_id = result['video_id']
        if video_id not in aggregated or result['similarity_score'] > aggregated[video_id]['similarity_score']:
            if video_id in aggregated:
                # Merge matching features
                result['matching_features'] = list(set(result['matching_features'] + aggregated[video_id]['matching_features']))
            aggregated[video_id] = result
    
    # Sort by similarity score
    final_results = list(aggregated.values())
    final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    # Limit results
    final_results = final_results[:request.max_results]
    
    return SimilaritySearchResponse(
        results=[SimilarityResult(**result) for result in final_results],
        total_results=len(final_results),
        query_video_id=request.video_id,
        threshold=request.threshold
    )
