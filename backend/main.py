"""
Main entry point for the FastAPI application.
"""
import logging
import sys
from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from app.routes import health, tasks, auth
import app.routes.gmail as gmail

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="An autonomous AI agent for task extraction and workflow execution",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list + ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "13.61.146.129",
        "13.61.146.129:8000","ec2-13-61-146-129.eu-north-1.compute.amazonaws.com",
                  "ec2-13-61-146-129.eu-north-1.compute.amazonaws.com:8000",
                  "auto-task-app.duckdns.org", "*.duckdns.org"]
)

# Include routers
app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(gmail.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    from app.database import engine, Base
    from app.models.db_models import DBTask  # Ensure models are imported
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("=" * 50)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")
    logger.info(f"LLM Model: {settings.model_name}")
    logger.info("=" * 50)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("=" * 50)
    logger.info("Shutting down API")
    logger.info("=" * 50)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    
    from starlette.exceptions import HTTPException as StarletteHTTPException
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
        
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
