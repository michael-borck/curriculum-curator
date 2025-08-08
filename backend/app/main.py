"""
Curriculum Curator - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Curriculum Curator...")
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Curriculum Curator",
    description="Pedagogically-aware course content platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers with error handling
try:
    from app.api.routes import auth, content, courses, llm

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
    app.include_router(content.router, prefix="/api/content", tags=["content"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
except ImportError as e:
    logger.warning(f"Some routes not loaded: {e}")


@app.get("/")
async def root():
    return {
        "message": "Curriculum Curator API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "curriculum-curator"}
