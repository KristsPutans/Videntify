"""API Service

This module provides the main API service for the VidID video identification system,
combining video management, identification, and user authentication endpoints.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.matching_engine import MatchingEngine, MatchResult, MatchingAlgorithm
from src.core.feature_extraction import FeatureExtractionEngine, FeatureType
from src.db.database import DatabaseManager
from src.db.models import Query, QueryResult, User
from src.utils.auth import get_current_user, create_access_token

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VidID API",
    description="API for video identification",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
async def get_db(db_manager=Depends(lambda: app.state.db_manager)):
    return db_manager.get_db_session()

# Dependency to get matching engine
async def get_matching_engine(db_manager=Depends(lambda: app.state.db_manager)):
    return app.state.matching_engine

# Dependency to get feature extraction engine
async def get_feature_engine(db_manager=Depends(lambda: app.state.db_manager)):
    return app.state.feature_engine


# Pydantic models for request/response validation
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_admin: bool


class VideoIdentificationRequest(BaseModel):
    matching_algorithms: List[MatchingAlgorithm] = Field(
        default=[MatchingAlgorithm.ENSEMBLE],
        description="Matching algorithms to use"
    )
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return")


class MatchResultResponse(BaseModel):
    content_id: str
    title: str
    confidence: float
    match_type: str
    timestamp: Optional[float] = None
    additional_metadata: Dict[str, Any] = {}


class VideoIdentificationResponse(BaseModel):
    query_id: str
    processing_time: float
    matches: List[MatchResultResponse]
    total_matches: int


# Authentication routes
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and get an access token."""
    # This would normally validate the username and password
    # For now, just return a simple token
    return {
        "access_token": create_access_token({"sub": request.username}),
        "token_type": "bearer"
    }


@app.post("/auth/register", response_model=UserResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # This would normally check if the username/email already exists
    # and hash the password before storing it
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        password_hash="hashed_password",  # This should be properly hashed
        created_at=datetime.utcnow(),
        is_admin=False
    )
    
    # In a real implementation, we would add the user to the database
    # db.add(user)
    # db.commit()
    
    return UserResponse(
        id=user_id,
        username=request.username,
        email=request.email,
        created_at=user.created_at,
        is_admin=user.is_admin
    )


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current user's information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        is_admin=current_user.is_admin
    )


# Video identification routes
@app.post("/identify/video", response_model=VideoIdentificationResponse)
async def identify_video(
    params: VideoIdentificationRequest = Depends(),
    video_file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    matching_engine: MatchingEngine = Depends(get_matching_engine),
    feature_engine: FeatureExtractionEngine = Depends(get_feature_engine),
    db: Session = Depends(get_db)
):
    """Identify a video clip."""
    start_time = datetime.utcnow()
    
    # Generate a unique ID for this query
    query_id = str(uuid.uuid4())
    
    # Save the uploaded file
    file_path = f"/tmp/{query_id}.mp4"
    with open(file_path, "wb") as buffer:
        buffer.write(await video_file.read())
    
    # Extract features from the video
    features = feature_engine.process_full_video(
        file_path, 
        [FeatureType.PERCEPTUAL_HASH, FeatureType.CNN_FEATURES, FeatureType.MOTION_PATTERN]
    )
    
    # Match the video against the database
    match_results = await matching_engine.match_video(
        features, 
        params.matching_algorithms,
        params.max_results
    )
    
    # Calculate processing time
    end_time = datetime.utcnow()
    processing_time = (end_time - start_time).total_seconds() * 1000  # in milliseconds
    
    # Log the query in the database
    # In a real implementation, we would save the query and results to the database
    
    # Convert MatchResult objects to MatchResultResponse objects
    match_responses = [
        MatchResultResponse(
            content_id=result.content_id,
            title=result.title,
            confidence=result.confidence,
            match_type=result.match_type,
            timestamp=result.timestamp,
            additional_metadata=result.additional_metadata
        ) for result in match_results
    ]
    
    return VideoIdentificationResponse(
        query_id=query_id,
        processing_time=processing_time,
        matches=match_responses,
        total_matches=len(match_responses)
    )


@app.post("/identify/frame")
async def identify_frame(
    frame_file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    matching_engine: MatchingEngine = Depends(get_matching_engine),
    feature_engine: FeatureExtractionEngine = Depends(get_feature_engine),
    db: Session = Depends(get_db)
):
    """Identify a single video frame."""
    # Implementation would be similar to identify_video but for a single frame
    # For now, return a placeholder response
    return {"message": "Not implemented yet"}


# Webhook for async processing
@app.post("/webhooks/identification-complete")
async def identification_complete_webhook(
    payload: Dict[str, Any] = Body(...),
    signature: str = Header(None, alias="X-Signature")
):
    """Webhook endpoint for async identification completion."""
    # Verify the webhook signature
    # Process the identification result
    return {"status": "accepted"}


# Import our API routers
from src.api.video_management import router as video_router
from src.api.identification import router as identification_router

# Include our routers
app.include_router(video_router, prefix="/api")
app.include_router(identification_router, prefix="/api")

# Initialize the app with required services
@app.on_event("startup")
async def startup_event():
    """Initialize the app with required services."""
    logger.info("Starting up VidID API")
    
    # Load configuration
    from src.config.config import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.get_all()
    app.state.config = config
    
    # Initialize database manager
    db_manager = DatabaseManager(config)
    app.state.db_manager = db_manager
    
    # Initialize feature extraction engine
    feature_engine = FeatureExtractionEngine(config)
    app.state.feature_engine = feature_engine
    
    # Initialize matching engine
    matching_engine = MatchingEngine(config, db_manager.vector_db_client, db_manager.get_db_session())
    app.state.matching_engine = matching_engine
    
    # Initialize object storage
    from src.utils.storage import create_storage
    app.state.object_storage = create_storage(config)
    
    # Create database tables if they don't exist
    db_manager.create_tables()
    
    logger.info("VidID API initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down VidID API")
    # Cleanup code here
