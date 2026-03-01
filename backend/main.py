"""
PharmaPricing MVP - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse
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
# Supports comma-separated values in CORS_ORIGINS (preferred) or FRONTEND_URL.
def _parse_allowed_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS") or os.getenv("FRONTEND_URL", "")
    origins = []
    for origin in raw_origins.split(","):
        origin = origin.strip()
        if not origin:
            continue
        # Normalize trailing slash to avoid exact-match failures in CORS checks.
        origins.append(origin.rstrip("/"))

    # Local development defaults
    origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ])

    # Deduplicate while preserving order
    deduped = []
    seen = set()
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            deduped.append(origin)
    return deduped


_allowed_origins = _parse_allowed_origins()
logger.info(f"CORS allowed origins: {_allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail if isinstance(exc.detail, str) else "HTTP_ERROR",
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "status_code": exc.status_code
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle unexpected exceptions
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "status_code": 500
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 3000)),
        reload=os.getenv("APP_ENV") == "development"
    )
