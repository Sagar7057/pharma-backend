"""
PharmaPricing MVP - FastAPI Backend
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 🔥 LOAD ENV FIRST — BEFORE ANYTHING ELSE
BASE_DIR = Path(__file__).resolve().parent

if os.getenv("APP_ENV") == "production":
    load_dotenv(BASE_DIR / ".env")
else:
    load_dotenv(BASE_DIR / ".env.local")

# NOW safe to import other modules
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from sqlalchemy import text
from app.database import engine  # 👈 now safe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    logger.info(f"Database configured: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
    yield
    # Shutdown
    logger.info("🛑 PharmaPricing API Server Shutting Down...")


# Create FastAPI app (ONLY ONCE)
app = FastAPI(
    title="PharmaPricing API",
    description="Pharmacy Distributor Pricing SaaS Platform",
    version="1.0.0",
    lifespan=lifespan
)

# -------------------------
# Middleware Configuration
# -------------------------

# CORS
_raw_origins = os.getenv("FRONTEND_URL", "http://localhost:3000")
_allowed_origins = list(
    set(
        [o.strip() for o in _raw_origins.split(",") if o.strip()]
        + ["http://localhost:3000", "http://localhost:5173"]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZIP Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# -------------------------
# Import Routes (AFTER app creation)
# -------------------------

from app.routes import (
    auth_routes,
    brand_routes,
    pricing_routes,
    quote_routes,
    analytics_routes,
    export_routes
)

# -------------------------
# Basic Endpoints
# -------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development")
    }


@app.get("/")
async def root():
    return {
        "message": "PharmaPricing API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/db-test")
async def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"db_response": result.scalar()}

# -------------------------
# Include Routers
# -------------------------

app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(brand_routes.router, prefix="/api/brands", tags=["Brands"])
app.include_router(pricing_routes.router, prefix="/api", tags=["Pricing"])
app.include_router(quote_routes.router, prefix="/api/quotes", tags=["Quotes"])
app.include_router(analytics_routes.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(export_routes.router, prefix="/api", tags=["Export"])


# -------------------------
# 404 Handler
# -------------------------

@app.get("/api/{path_name:path}")
async def not_found(path_name: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Endpoint not found"
    )


# -------------------------
# Exception Handlers
# -------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return {
        "error": {
            "code": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status_code": 500
        }
    }


# -------------------------
# Local Development Entry
# -------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 3000)),
        reload=os.getenv("APP_ENV", "development") == "development"
    )
