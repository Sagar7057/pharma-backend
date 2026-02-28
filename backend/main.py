"""
PharmaPricing MVP - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from app.routes import auth_routes, brand_routes, pricing_routes, quote_routes, analytics_routes, export_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events
    """
    # Startup
    logger.info("🚀 PharmaPricing API Server Starting...")
    logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
    logger.info(f"Database: {os.getenv('DATABASE_URL', 'Not configured')}")
    yield
    # Shutdown
    logger.info("🛑 PharmaPricing API Server Shutting Down...")

# Create FastAPI app
app = FastAPI(
    title="PharmaPricing API",
    description="Pharmacy Distributor Pricing SaaS Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZIP compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development")
    }

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "PharmaPricing API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Include routes
app.include_router(
    auth_routes.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    brand_routes.router,
    prefix="/api/brands",
    tags=["Brands"]
)

app.include_router(
    pricing_routes.router,
    prefix="/api",
    tags=["Pricing"]
)

app.include_router(
    quote_routes.router,
    prefix="/api/quotes",
    tags=["Quotes"]
)

app.include_router(
    analytics_routes.router,
    prefix="/api/analytics",
    tags=["Analytics"]
)

app.include_router(
    export_routes.router,
    prefix="/api",
    tags=["Export"]
)

# 404 handler
@app.get("/api/{path_name:path}")
async def not_found(path_name: str):
    """
    404 handler for undefined API routes
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Endpoint not found"
    )

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Custom HTTP exception handler
    """
    return {
        "error": {
            "code": exc.detail if isinstance(exc.detail, str) else "HTTP_ERROR",
            "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "status_code": exc.status_code
        }
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle unexpected exceptions
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status_code": 500
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 3000)),
        reload=os.getenv("APP_ENV") == "development"
    )
