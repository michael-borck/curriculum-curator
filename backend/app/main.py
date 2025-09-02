"""
Curriculum Curator - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from slowapi.errors import RateLimitExceeded

# CSRF removed - using JWT + CORS instead
from app.core.database import SessionLocal, init_db
from app.core.password_validator import PasswordValidator
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.core.security_middleware import (
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
    TrustedProxyMiddleware,
)
from app.core.security_utils import SecurityManager
from app.core.startup_checks import run_startup_checks
from app.services.git_content_service import get_git_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Curriculum Curator...")
    try:
        init_db()
        logger.info("✅ Database initialized")

        # Run startup checks and cleanup
        db = SessionLocal()
        try:
            run_startup_checks(db)
        finally:
            db.close()

        # Initialize Git repository for content
        git_service = get_git_service()
        logger.info(f"✅ Git repository initialized at {git_service.repo_path}")

        # Initialize configuration service
        from app.services.config_service import ConfigService  # noqa: PLC0415

        db = SessionLocal()
        try:
            ConfigService.initialize(db)
            logger.info("✅ Configuration service initialized")
        finally:
            db.close()

    except Exception as e:
        logger.warning(f"Initialization warning: {e}")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Curriculum Curator",
    description="Pedagogically-aware course content platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiting to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Security middleware (order matters - add from outermost to innermost)
# 1. Trusted host validation (first line of defense)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.localhost",
        "*.edu",
        "*",
    ],  # Adjust for production
)

# 2. Request validation and basic security checks
app.add_middleware(
    RequestValidationMiddleware,
    max_request_size=10 * 1024 * 1024,  # 10MB limit
    require_user_agent=False,  # Set to True for stricter validation
)

# 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. Trusted proxy handling (for load balancers/reverse proxies)
app.add_middleware(
    TrustedProxyMiddleware,
    trusted_proxies=["127.0.0.1", "::1"],  # Add your proxy IPs here
)

# 5. CORS configuration (should be last middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers with individual error handling
# Critical routes first - auth should always load
try:
    from app.api.routes import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
except ImportError as e:
    logger.error(f"Failed to load auth routes: {e}")

try:
    from app.api.routes import admin
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
except ImportError as e:
    logger.warning(f"Failed to load admin routes: {e}")

try:
    from app.api.routes import admin_config
    app.include_router(admin_config.router, prefix="/api/admin", tags=["admin-config"])
except ImportError as e:
    logger.warning(f"Failed to load admin_config routes: {e}")

try:
    from app.api.routes import courses
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
except ImportError as e:
    logger.warning(f"Failed to load courses routes: {e}")

try:
    from app.api.routes import units
    app.include_router(units.router, prefix="/api/units", tags=["units"])
except ImportError as e:
    logger.warning(f"Failed to load units routes: {e}")

try:
    from app.api.routes import unit_structure
    app.include_router(unit_structure.router, prefix="/api", tags=["unit-structure"])
except ImportError as e:
    logger.warning(f"Failed to load unit_structure routes: {e}")

try:
    from app.api.routes import learning_outcomes
    app.include_router(
        learning_outcomes.router, prefix="/api/outcomes", tags=["learning-outcomes"]
    )
except ImportError as e:
    logger.warning(f"Failed to load learning_outcomes routes: {e}")

try:
    from app.api.routes import materials
    app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
except ImportError as e:
    logger.warning(f"Failed to load materials routes: {e}")

try:
    from app.api.routes import assessments
    app.include_router(
        assessments.router, prefix="/api/assessments", tags=["assessments"]
    )
except ImportError as e:
    logger.warning(f"Failed to load assessments routes: {e}")

try:
    from app.api.routes import analytics
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
except ImportError as e:
    logger.warning(f"Failed to load analytics routes: {e}")

try:
    from app.api.routes import content
    app.include_router(content.router, prefix="/api/content", tags=["content"])
except ImportError as e:
    logger.warning(f"Failed to load content routes: {e}")

try:
    from app.api.routes import content_export
    app.include_router(content_export.router, prefix="/api", tags=["export"])
except ImportError as e:
    logger.warning(f"Failed to load content_export routes: {e}")

try:
    from app.api.routes import content_versions
    app.include_router(content_versions.router, prefix="/api", tags=["versions"])
except ImportError as e:
    logger.warning(f"Failed to load content_versions routes: {e}")

try:
    from app.api.routes import import_content
    app.include_router(import_content.router, prefix="/api/content", tags=["import"])
except ImportError as e:
    logger.warning(f"Failed to load import_content routes: {e}")

try:
    from app.api.routes import content_workflow
    app.include_router(
        content_workflow.router, prefix="/api/content", tags=["workflow"]
    )
except ImportError as e:
    logger.warning(f"Failed to load content_workflow routes: {e}")

try:
    from app.api.routes import llm
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
except ImportError as e:
    logger.warning(f"Failed to load llm routes: {e}")

try:
    from app.api.routes import llm_config
    app.include_router(llm_config.router, prefix="/api/llm-config", tags=["llm-config"])
except ImportError as e:
    logger.warning(f"Failed to load llm_config routes: {e}")

try:
    from app.api.routes import ai
    app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
except ImportError as e:
    logger.warning(f"Failed to load ai routes: {e}")

try:
    from app.api.routes import user_export
    app.include_router(user_export.router, prefix="/api/user", tags=["user"])
except ImportError as e:
    logger.warning(f"Failed to load user_export routes: {e}")

try:
    from app.api.routes import monitoring
    app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
except ImportError as e:
    logger.warning(f"Failed to load monitoring routes: {e}")


# Remove the root API endpoint - let static files handle it


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "curriculum-curator"}


@app.get("/security/stats")
async def security_stats():
    """Get basic security statistics (admin only in production)"""

    db = SessionLocal()
    try:
        return SecurityManager.get_security_stats(db, hours=24)
    finally:
        db.close()


@app.post("/password-strength")
async def check_password_strength(request: Request):
    """Check password strength (for real-time frontend feedback)"""
    body = await request.json()
    password = body.get("password", "")
    name = body.get("name", "")
    email = body.get("email", "")

    is_valid, errors = PasswordValidator.validate_password(password, name, email)
    strength_score, strength_desc = PasswordValidator.get_password_strength_score(
        password
    )
    suggestions = (
        PasswordValidator.suggest_improvements(password, errors) if not is_valid else []
    )

    return {
        "is_valid": is_valid,
        "errors": errors,
        "suggestions": suggestions,
        "strength_score": strength_score,
        "strength": strength_desc,
    }


# Debug endpoint for testing
@app.post("/test-form")
async def test_form_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
    """Test endpoint to debug form data"""
    return {
        "username": form_data.username,
        "password": "hidden",
        "grant_type": form_data.grant_type,
        "scopes": form_data.scopes,
    }


# Serve static files - MUST BE LAST (after all API routes)
# Check if we're in Docker container (frontend is built)
frontend_path = Path("/app/frontend/dist")
if not frontend_path.exists():
    # Development mode - look for frontend in parent directory
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / "dist"

if frontend_path.exists():
    # Mount static files at root, but only for non-API routes
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")
    
    # Catch-all route for SPA - serves index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't serve index.html for API routes
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        
        # Serve index.html for all other routes (SPA routing)
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"detail": "Frontend not found"}
else:
    logger.warning(f"Frontend build not found at {frontend_path}")
