"""Admin Dashboard

This module provides a web-based admin dashboard for monitoring the VidID system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import Video, Query, QueryResult, User
from src.utils.auth import get_current_admin_user

logger = logging.getLogger(__name__)

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router for admin dashboard
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(current_user: User = Depends(get_current_admin_user)):
    """Admin dashboard home page."""
    # In a real implementation, this would render a template with dashboard data
    return "<html><body><h1>VidID Admin Dashboard</h1><p>Welcome, Admin!</p></body></html>"


@router.get("/content-ingestion")
async def content_ingestion_monitoring(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends()
):
    """Monitor content ingestion."""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query for videos ingested in the date range
    videos = db.query(Video).filter(
        Video.ingestion_date >= start_date,
        Video.ingestion_date <= end_date
    ).all()
    
    # Group by day and source
    ingestion_stats = {}
    for video in videos:
        day = video.ingestion_date.date().isoformat()
        source = video.source.value
        
        if day not in ingestion_stats:
            ingestion_stats[day] = {}
            
        if source not in ingestion_stats[day]:
            ingestion_stats[day][source] = 0
            
        ingestion_stats[day][source] += 1
    
    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "total_videos": len(videos),
        "daily_stats": ingestion_stats
    }


@router.get("/system-performance")
async def system_performance_metrics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends()
):
    """System performance metrics."""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query for queries in the date range
    queries = db.query(Query).filter(
        Query.created_at >= start_date,
        Query.created_at <= end_date
    ).all()
    
    # Calculate performance metrics
    performance_data = {
        "total_queries": len(queries),
        "avg_processing_time": 0,
        "success_rate": 0,
        "daily_query_count": {}
    }
    
    if queries:
        # Calculate average processing time
        total_processing_time = sum(q.processing_time for q in queries if q.processing_time is not None)
        processing_time_count = sum(1 for q in queries if q.processing_time is not None)
        
        if processing_time_count > 0:
            performance_data["avg_processing_time"] = total_processing_time / processing_time_count
        
        # Calculate success rate
        success_count = sum(1 for q in queries if q.success is True)
        if queries:
            performance_data["success_rate"] = (success_count / len(queries)) * 100
        
        # Group queries by day
        for query in queries:
            day = query.created_at.date().isoformat()
            
            if day not in performance_data["daily_query_count"]:
                performance_data["daily_query_count"][day] = 0
                
            performance_data["daily_query_count"][day] += 1
    
    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "performance": performance_data
    }


@router.get("/user-analytics")
async def user_analytics(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends()
):
    """User analytics and trending queries."""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get user statistics
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(
        User.last_login >= start_date
    ).scalar()
    new_users = db.query(func.count(User.id)).filter(
        User.created_at >= start_date
    ).scalar()
    
    # Get top users by query count
    user_query_counts = db.query(
        Query.user_id,
        func.count(Query.id).label("query_count")
    ).filter(
        Query.created_at >= start_date,
        Query.user_id.isnot(None)
    ).group_by(Query.user_id).order_by(func.count(Query.id).desc()).limit(10).all()
    
    top_users = []
    for user_id, query_count in user_query_counts:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            top_users.append({
                "user_id": user_id,
                "username": user.username,
                "query_count": query_count
            })
    
    # Get trending queries (most common matched videos)
    trending_content = db.query(
        QueryResult.video_id,
        func.count(QueryResult.id).label("match_count")
    ).filter(
        QueryResult.created_at >= start_date
    ).group_by(QueryResult.video_id).order_by(func.count(QueryResult.id).desc()).limit(10).all()
    
    trending = []
    for video_id, match_count in trending_content:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            trending.append({
                "video_id": video_id,
                "title": video.title,
                "match_count": match_count
            })
    
    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "user_stats": {
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users
        },
        "top_users": top_users,
        "trending_content": trending
    }


@router.get("/catalog-stats")
async def catalog_statistics(current_user: User = Depends(get_current_admin_user), db: Session = Depends()):
    """Catalog statistics."""
    # Get total video count
    total_videos = db.query(func.count(Video.id)).scalar()
    
    # Get video counts by source
    source_counts = db.query(
        Video.source,
        func.count(Video.id).label("count")
    ).group_by(Video.source).all()
    
    sources = {source.value: count for source, count in source_counts}
    
    # Get video counts by content type
    type_counts = db.query(
        Video.content_type,
        func.count(Video.id).label("count")
    ).group_by(Video.content_type).all()
    
    content_types = {content_type.value: count for content_type, count in type_counts}
    
    # Get total duration of all videos
    total_duration = db.query(func.sum(Video.duration)).scalar() or 0
    
    return {
        "total_videos": total_videos,
        "total_duration_hours": total_duration / 3600,
        "by_source": sources,
        "by_content_type": content_types
    }


@router.get("/system-health")
async def system_health(current_user: User = Depends(get_current_admin_user)):
    """System health monitoring."""
    # In a real implementation, this would query various system metrics
    # For now, return placeholder data
    return {
        "status": "healthy",
        "components": {
            "api": {"status": "ok", "latency_ms": 42},
            "database": {"status": "ok", "connection_pool": {"used": 3, "available": 17}},
            "feature_extraction": {"status": "ok", "queue_size": 0},
            "matching_engine": {"status": "ok", "avg_response_time_ms": 156}
        },
        "resources": {
            "cpu_usage": 35.2,
            "memory_usage": 62.7,
            "disk_usage": 48.3
        }
    }
