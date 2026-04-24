"""
Health check endpoint for the API.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Dictionary with health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Autonomous AI Agent API",
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        Welcome message with API info
    """
    return {
        "message": "Welcome to Autonomous AI Agent API",
        "documentation": "/docs",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "tasks": "/api/tasks",
            "workflows": "/api/workflows",
            "emails": "/api/emails"
        }
    }