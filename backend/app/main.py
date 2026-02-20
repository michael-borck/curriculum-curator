"""
Curriculum Curator - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

# CSRF removed - using JWT + CORS instead
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.password_validator import PasswordValidator
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.core.security import get_password_hash
from app.core.security_middleware import (
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
    TrustedProxyMiddleware,
)
from app.services.git_content_service import get_git_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _seed_ollama_config() -> None:
    """Create a default (inactive) Ollama LLM configuration for LOCAL_MODE."""
    from app.api.deps import LOCAL_USER_ID  # noqa: PLC0415
    from app.models.llm_config import LLMConfiguration  # noqa: PLC0415

    if SessionLocal is None:
        return

    db = SessionLocal()
    try:
        existing = (
            db.query(LLMConfiguration)
            .filter(
                LLMConfiguration.user_id == LOCAL_USER_ID,
                LLMConfiguration.provider == "ollama",
            )
            .first()
        )
        if existing:
            logger.info("Ollama LLM config already exists")
            return

        config = LLMConfiguration(
            user_id=LOCAL_USER_ID,
            provider="ollama",
            api_url=settings.OLLAMA_BASE_URL,
            model_name="ollama/llama3.2",
            temperature=0.7,
            is_default=False,
            is_active=False,
        )
        db.add(config)
        db.commit()
        logger.info("Seeded default Ollama LLM config (inactive)")
    except Exception:
        db.rollback()
        logger.exception("Failed to seed Ollama config")
    finally:
        db.close()


def _seed_local_user() -> None:
    """Create the default local user if it doesn't already exist."""
    from app.api.deps import LOCAL_USER_EMAIL, LOCAL_USER_ID  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415

    if SessionLocal is None:
        logger.warning("Cannot seed local user: database not configured")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.id == LOCAL_USER_ID).first()
        if existing:
            logger.info(f"✅ Local user already exists: {LOCAL_USER_EMAIL}")
            return

        local_user = User(
            id=LOCAL_USER_ID,
            email=LOCAL_USER_EMAIL,
            password_hash=get_password_hash("local-mode-no-password"),
            name="Local User",
            role="lecturer",
            is_verified=True,
            is_active=True,
        )
        db.add(local_user)
        db.commit()
        logger.info(f"✅ Local user created: {LOCAL_USER_EMAIL} (admin)")
    except Exception:
        db.rollback()
        logger.exception("Failed to seed local user")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Curriculum Curator...")
    try:
        init_db()
        logger.info("✅ Database initialized")

        # Run startup checks and cleanup (skipped for now - migrating to raw SQLite)
        # TODO: Migrate startup_checks and config_service to raw SQLite
        logger.info("⚠️ Startup checks skipped (pending raw SQLite migration)")

        # Initialize Git content service (per-unit repos)
        git_service = get_git_service()
        logger.info(f"✅ Git content service initialized at {git_service.repos_base}")

        # LOCAL_MODE: seed the default local user and Ollama config
        if settings.LOCAL_MODE:
            _seed_local_user()
            _seed_ollama_config()

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
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]


# Add validation exception handler for debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"[VALIDATION ERROR] Path: {request.url.path}")
    logger.error(f"[VALIDATION ERROR] Method: {request.method}")
    logger.error(f"[VALIDATION ERROR] Details: {exc.errors()}")

    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = dict(error)
        # Convert any exception objects in ctx to strings
        if "ctx" in error_dict and isinstance(error_dict["ctx"], dict):
            error_dict["ctx"] = {
                k: str(v) if isinstance(v, Exception) else v
                for k, v in error_dict["ctx"].items()
            }
        errors.append(error_dict)

    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": str(exc.body)},
    )


# Add middleware to debug all requests to /api/units
@app.middleware("http")
async def debug_units_requests(request: Request, call_next):
    if "/units" in request.url.path:
        logger.info(f"[MIDDLEWARE] {request.method} {request.url.path}")
        logger.info(f"[MIDDLEWARE] Headers: {dict(request.headers)}")
        logger.info(f"[MIDDLEWARE] Content-Type: {request.headers.get('content-type')}")

    response = await call_next(request)

    if "/units" in request.url.path:
        logger.info(f"[MIDDLEWARE] Response status: {response.status_code}")

    return response


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
    trusted_proxies=[
        "127.0.0.1",
        "::1",
        "172.17.0.1",  # Docker default bridge
        "172.18.0.1",  # Docker network
        "172.19.0.1",  # Docker network
        "172.20.0.1",  # Docker network
        "172.21.0.1",  # Docker network
        "172.22.0.1",  # Docker network (Caddy)
        "host.docker.internal",  # Docker host
    ],
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
except ImportError:
    logger.exception("Failed to load auth routes")

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
    from app.api.routes import units

    app.include_router(units.router, prefix="/api/units", tags=["units"])
    logger.info("✅ Units routes loaded successfully")
    # Log all registered routes for debugging
    for route in units.router.routes:
        if isinstance(route, APIRoute) and route.methods:
            logger.info(f"  → {route.path} [{', '.join(route.methods)}]")
            # Log the actual endpoint function for POST routes
            if "POST" in route.methods:
                logger.info(f"      Endpoint: {route.endpoint.__name__}")
                if hasattr(route, "dependant") and hasattr(
                    route.dependant, "dependencies"
                ):
                    logger.info(
                        f"      Dependencies: {len(route.dependant.dependencies)} items"
                    )
except ImportError:
    logger.exception("❌ Failed to load units routes")

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
    from app.api.routes import accreditation

    app.include_router(
        accreditation.router, prefix="/api/accreditation", tags=["accreditation"]
    )
except ImportError as e:
    logger.warning(f"Failed to load accreditation routes: {e}")

try:
    from app.api.routes import content

    # Content routes are nested under units: /api/units/{unit_id}/content
    app.include_router(
        content.router, prefix="/api/units/{unit_id}/content", tags=["content"]
    )
except ImportError as e:
    logger.warning(f"Failed to load content routes: {e}")

try:
    from app.api.routes import content_export

    app.include_router(content_export.router, prefix="/api", tags=["export"])
except ImportError as e:
    logger.warning(f"Failed to load content_export routes: {e}")

# content_versions removed - version control now via Git in content routes

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
    from app.api.routes import llm_config

    app.include_router(llm_config.router, prefix="/api/llm-config", tags=["llm-config"])
except ImportError as e:
    logger.warning(f"Failed to load llm_config routes: {e}")

try:
    from app.api.routes import ai

    # AI routes handle all LLM functionality (merged from /api/llm and /api/ai)
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

try:
    from app.api.routes import web_search

    app.include_router(web_search.router, prefix="/api/search", tags=["search"])
except ImportError as e:
    logger.warning(f"Failed to load web_search routes: {e}")

try:
    from app.api.routes import research_sources

    app.include_router(
        research_sources.router, prefix="/api/sources", tags=["research-sources"]
    )
except ImportError as e:
    logger.warning(f"Failed to load research_sources routes: {e}")

try:
    from app.api.routes import ollama

    app.include_router(ollama.router, prefix="/api/ollama", tags=["ollama"])
except ImportError as e:
    logger.warning(f"Failed to load ollama routes: {e}")

try:
    from app.api.routes import imscc_export

    app.include_router(imscc_export.router, prefix="/api", tags=["imscc-export"])
except ImportError as e:
    logger.warning(f"Failed to load imscc_export routes: {e}")


# Remove the root API endpoint - let static files handle it


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "curriculum-curator"}


@app.get("/security/stats")
async def security_stats():
    """Get basic security statistics (admin only in production)"""
    # TODO: Migrate to raw SQLite security_repo
    return {
        "period_hours": 24,
        "total_login_attempts": 0,
        "failed_attempts": 0,
        "success_rate": 100.0,
        "currently_locked_accounts": 0,
        "unique_ip_addresses": 0,
        "note": "Security stats temporarily unavailable during SQLite migration",
    }


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
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets"
    )

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
