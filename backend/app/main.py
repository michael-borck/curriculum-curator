"""
Curriculum Curator - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# Import and include routers with error handling
try:
    from app.api.routes import (
        admin,
        admin_config,
        ai,
        auth,
        content,
        content_workflow,
        course_modules,
        courses,
        export,
        import_content,
        llm,
        lrds,
        materials,
        materials_git,
        monitoring,
        plugins,
        tasks,
        user_export,
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(admin_config.router, prefix="/api/admin", tags=["admin-config"])
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
    app.include_router(course_modules.router, prefix="/api", tags=["course-modules"])
    app.include_router(content.router, prefix="/api/content", tags=["content"])
    app.include_router(import_content.router, prefix="/api/content", tags=["import"])
    app.include_router(content_workflow.router, prefix="/api/content", tags=["workflow"])
    app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
    app.include_router(materials_git.router, prefix="/api/materials", tags=["materials-git"])
    app.include_router(export.router, prefix="/api/export", tags=["export"])
    app.include_router(lrds.router, prefix="/api/lrds", tags=["lrds"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
    app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
    app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])
    app.include_router(user_export.router, prefix="/api/user", tags=["user"])
    app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
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
