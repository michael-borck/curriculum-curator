import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from curriculum_curator.config.utils import load_config
from curriculum_curator.core import CurriculumCurator
from curriculum_curator.web.models import (
    PromptTemplate,
    WorkflowSession,
    create_database_engine,
    get_session_factory,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(title="Curriculum Curator API", version="0.2.1")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_database_engine()
SessionLocal = get_session_factory(engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Global variables
curator_instance = None
config = None


# Pydantic models for API
class WorkflowRunRequest(BaseModel):
    workflow: str
    variables: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    session_id: str
    status: str
    message: str


class WorkflowListResponse(BaseModel):
    config_workflows: Dict[str, Any]
    predefined_workflows: Dict[str, Any]


class PromptListResponse(BaseModel):
    prompts: List[str]


class ValidatorInfo(BaseModel):
    name: str
    implemented: bool
    category: str


class RemediatorInfo(BaseModel):
    name: str
    implemented: bool
    category: str


# Initialize the application
@app.on_event("startup")
async def startup_event():
    global curator_instance, config
    try:
        config_path = Path("config.yaml")
        if not config_path.exists():
            logger.warning("config.yaml not found, using default configuration")
            config = {}
        else:
            config = load_config(str(config_path))
        curator_instance = CurriculumCurator(config)
        logger.info("Curriculum Curator initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Curriculum Curator", error=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Curriculum Curator API is running"}


# Workflow endpoints
@app.get("/api/workflows", response_model=WorkflowListResponse)
async def list_workflows():
    """List available workflows."""
    try:
        import inspect

        from curriculum_curator.workflow import workflows as workflows_module

        # Load config workflows
        config_workflows = {}
        if hasattr(config, "workflows"):
            config_workflows = config.workflows
        elif isinstance(config, dict) and "workflows" in config:
            config_workflows = config["workflows"]

        # Load predefined workflows
        predefined_workflows = {}
        for _name, value in inspect.getmembers(workflows_module):
            if isinstance(value, dict) and "name" in value and "description" in value:
                predefined_workflows[value["name"]] = value

        return WorkflowListResponse(
            config_workflows=config_workflows, predefined_workflows=predefined_workflows
        )
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRunRequest, db: Session = Depends(get_db)):
    """Run a workflow."""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Create workflow session record
        workflow_session = WorkflowSession(
            session_id=session_id,
            workflow_name=request.workflow,
            status="running",
            variables=json.dumps(request.variables),
        )
        db.add(workflow_session)
        db.commit()

        # Run workflow asynchronously in background
        asyncio.create_task(
            _run_workflow_background(session_id, request.workflow, request.variables, db)
        )

        return WorkflowRunResponse(
            session_id=session_id,
            status="running",
            message=f"Workflow '{request.workflow}' started successfully",
        )
    except Exception as e:
        logger.error("Failed to start workflow", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def _run_workflow_background(
    session_id: str, workflow_name: str, variables: Dict[str, Any], db: Session
):
    """Run workflow in background and update database."""
    try:
        # Run the workflow
        result = await curator_instance.run_workflow(workflow_name, variables, session_id)

        # Update session with success
        workflow_session = (
            db.query(WorkflowSession).filter(WorkflowSession.session_id == session_id).first()
        )
        if workflow_session:
            workflow_session.status = "completed"
            workflow_session.result = json.dumps(result, default=str)
            db.commit()

    except Exception as e:
        logger.error("Workflow failed", session_id=session_id, error=str(e))
        # Update session with error
        workflow_session = (
            db.query(WorkflowSession).filter(WorkflowSession.session_id == session_id).first()
        )
        if workflow_session:
            workflow_session.status = "failed"
            workflow_session.error_message = str(e)
            db.commit()


@app.get("/api/workflows/sessions/{session_id}")
async def get_workflow_session(session_id: str, db: Session = Depends(get_db)):
    """Get workflow session status and results."""
    workflow_session = (
        db.query(WorkflowSession).filter(WorkflowSession.session_id == session_id).first()
    )
    if not workflow_session:
        raise HTTPException(status_code=404, detail="Session not found")

    response_data = {
        "session_id": workflow_session.session_id,
        "workflow_name": workflow_session.workflow_name,
        "status": workflow_session.status,
        "variables": json.loads(workflow_session.variables) if workflow_session.variables else {},
        "created_at": workflow_session.created_at.isoformat(),
        "updated_at": workflow_session.updated_at.isoformat(),
    }

    if workflow_session.result:
        response_data["result"] = json.loads(workflow_session.result)
    if workflow_session.error_message:
        response_data["error_message"] = workflow_session.error_message

    return response_data


@app.get("/api/workflows/sessions")
async def list_workflow_sessions(db: Session = Depends(get_db)):
    """List all workflow sessions."""
    sessions = db.query(WorkflowSession).order_by(WorkflowSession.created_at.desc()).all()
    return [
        {
            "session_id": session.session_id,
            "workflow_name": session.workflow_name,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        for session in sessions
    ]


# Prompt endpoints
@app.get("/api/prompts", response_model=PromptListResponse)
async def list_prompts(tag: Optional[str] = None):
    """List available prompts."""
    try:
        prompts = curator_instance.list_prompts(tag)
        return PromptListResponse(prompts=prompts)
    except Exception as e:
        logger.error("Failed to list prompts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Validator endpoints
@app.get("/api/validators")
async def list_validators():
    """List available validators."""
    try:
        from curriculum_curator.validation.validators import VALIDATOR_REGISTRY

        categories = {
            "quality": [],
            "accuracy": [],
            "alignment": [],
            "style": [],
            "language": [],
            "safety": [],
        }

        for name, cls in VALIDATOR_REGISTRY.items():
            implemented = cls is not None
            
            # Categorize validators
            if "quality" in name or name in [
                "similarity",
                "structure",
                "readability",
                "completeness",
                "coherence",
                "consistency",
                "generic_detector",
            ]:
                category = "quality"
            elif "accuracy" in name or name in ["factuality", "references"]:
                category = "accuracy"
            elif "alignment" in name or name in [
                "objectives",
                "relevance",
                "age_appropriateness",
                "instruction_adherence",
            ]:
                category = "alignment"
            elif "style" in name or name in ["bias", "tone"]:
                category = "style"
            elif "language" in name or name in ["language_detector", "grammar", "spelling"]:
                category = "language"
            elif "safety" in name or name in ["content_safety"]:
                category = "safety"
            else:
                category = "quality"

            categories[category].append(ValidatorInfo(
                name=name, implemented=implemented, category=category
            ))

        return categories
    except Exception as e:
        logger.error("Failed to list validators", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Remediator endpoints
@app.get("/api/remediators")
async def list_remediators():
    """List available remediators."""
    try:
        from curriculum_curator.remediation.remediators import REMEDIATOR_REGISTRY

        categories = {"autofix": [], "rewrite": [], "workflow": [], "language": []}

        for name, cls in REMEDIATOR_REGISTRY.items():
            implemented = cls is not None

            if "format" in name or "sentence" in name or "terminology" in name:
                category = "autofix"
            elif "rewrite" in name or "rephrasing" in name:
                category = "rewrite"
            elif "workflow" in name or "flag" in name or "review" in name:
                category = "workflow"
            elif "language" in name or "translator" in name:
                category = "language"
            else:
                category = "autofix"

            categories[category].append(RemediatorInfo(
                name=name, implemented=implemented, category=category
            ))

        return categories
    except Exception as e:
        logger.error("Failed to list remediators", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files (React app will be built here)
try:
    app.mount("/", StaticFiles(directory="web/build", html=True), name="static")
except Exception:
    # During development, the build directory might not exist yet
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)