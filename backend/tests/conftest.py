"""
Pytest configuration for backend tests

Supports three test modes:
1. Unit tests with in-memory DB - service tests (test_*_service.py)
2. Unit tests without backend - mock-based (test_services_unit.py)
3. Integration tests - require running backend (test_auth*.py, test_basic.py)
"""

import os
import time
import uuid

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set environment variables before importing app modules
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///")

from app.core.database import Base
from app.models import (
    Unit,
    UnitOutline,
    UnitStructureStatus,
    User,
    UserRole,
)
from app.models.accreditation_mappings import (
    ULOGraduateCapabilityMapping,
    UnitAoLMapping,
    UnitSDGMapping,
)
from app.models.assessment import Assessment, AssessmentType
from app.models.content import Content, ContentType
from app.models.learning_design import DesignStatus, LearningDesign
from app.models.learning_outcome import UnitLearningOutcome
from app.models.quiz_question import QuestionType, QuizQuestion
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


def is_backend_running() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# ──────────────────────────────────────────────────────────────
# Integration test fixtures (unchanged)
# ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API"""
    return BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """API URL for the backend"""
    return API_URL


@pytest.fixture(scope="session")
def backend_available():
    """Check if backend is available, skip integration tests if not"""
    if not is_backend_running():
        pytest.skip("Backend is not running - skipping integration tests")
    return True


@pytest.fixture
def unique_email():
    """Generate a unique test email"""
    timestamp = int(time.time() * 1000)
    return f"test{timestamp}@example.com"


# ──────────────────────────────────────────────────────────────
# In-memory SQLite fixtures for service tests
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database with all tables for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import all models to register them, then create tables
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Insert a real User row into the test database."""
    user = User(
        id=str(uuid.uuid4()),
        email="testuser@example.com",
        password_hash="hashed_password_placeholder",
        name="Test User",
        role=UserRole.LECTURER.value,
        is_verified=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_unit(test_db: Session, test_user: User) -> Unit:
    """Insert a real Unit row into the test database."""
    unit = Unit(
        id=str(uuid.uuid4()),
        title="Test Unit: Introduction to Testing",
        code="TEST1001",
        description="A unit for testing purposes",
        year=2026,
        semester="semester_1",
        pedagogy_type="inquiry-based",
        difficulty_level="intermediate",
        duration_weeks=12,
        owner_id=test_user.id,
        created_by_id=test_user.id,
        credit_points=6,
    )
    test_db.add(unit)
    test_db.commit()
    test_db.refresh(unit)
    return unit


@pytest.fixture
def client(test_db: Session, test_user: User):
    """FastAPI TestClient with dependency overrides for DB and auth.

    Uses in-memory SQLite and bypasses JWT authentication so tests exercise
    the full HTTP → route → service → DB → response chain.
    """
    from fastapi.testclient import TestClient

    from app.api import deps
    from app.main import app
    from app.schemas.user import UserResponse

    # GUID TypeDecorator returns uuid.UUID objects; UserResponse expects str
    user_dict = {
        "id": str(test_user.id),
        "email": test_user.email,
        "name": test_user.name,
        "role": test_user.role,
        "is_verified": test_user.is_verified,
        "is_active": test_user.is_active,
        "created_at": str(test_user.created_at)
        if test_user.created_at
        else "2026-01-01T00:00:00",
    }
    user_resp = UserResponse.model_validate(user_dict)

    # get_db is a generator, so the override must be too
    def _override_get_db():
        yield test_db

    app.dependency_overrides[deps.get_db] = _override_get_db
    app.dependency_overrides[deps.get_current_user] = lambda: user_resp
    app.dependency_overrides[deps.get_current_active_user] = lambda: user_resp

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_unit_outline(
    test_db: Session, test_unit: Unit, test_user: User
) -> UnitOutline:
    """Insert a real UnitOutline row into the test database."""
    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        title=test_unit.title,
        description="Test unit outline",
        duration_weeks=12,
        credit_points=6,
        status=UnitStructureStatus.PLANNING.value,
        created_by_id=test_user.id,
    )
    test_db.add(outline)
    test_db.commit()
    test_db.refresh(outline)
    return outline


# ──────────────────────────────────────────────────────────────
# Additional fixtures for export / assessment tests
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def test_assessment(test_db: Session, test_unit: Unit) -> Assessment:
    """Insert a real Assessment row into the test database."""
    assessment = Assessment(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        title="Quiz 1",
        type=AssessmentType.FORMATIVE.value,
        category="quiz",
        weight=20.0,
        description="Short quiz on fundamentals",
        due_week=4,
        status="draft",
    )
    test_db.add(assessment)
    test_db.commit()
    test_db.refresh(assessment)
    return assessment


@pytest.fixture
def test_weekly_topic(
    test_db: Session,
    test_unit_outline: UnitOutline,
    test_unit: Unit,
    test_user: User,
) -> WeeklyTopic:
    """Insert a real WeeklyTopic row into the test database."""
    topic = WeeklyTopic(
        id=str(uuid.uuid4()),
        unit_outline_id=test_unit_outline.id,
        unit_id=test_unit.id,
        week_number=1,
        topic_title="HTML Basics",
        created_by_id=test_user.id,
    )
    test_db.add(topic)
    test_db.commit()
    test_db.refresh(topic)
    return topic


@pytest.fixture
def test_weekly_material(test_db: Session, test_unit: Unit) -> WeeklyMaterial:
    """Insert a real WeeklyMaterial row into the test database."""
    material = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        week_number=1,
        title="HTML Lecture",
        type="lecture",
        description="<p>Introduction to HTML tags and structure.</p>",
        order_index=0,
    )
    test_db.add(material)
    test_db.commit()
    test_db.refresh(material)
    return material


@pytest.fixture
def test_ulo(test_db: Session, test_unit: Unit, test_user: User) -> UnitLearningOutcome:
    """Insert a real UnitLearningOutcome row into the test database."""
    ulo = UnitLearningOutcome(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        outcome_type="ulo",
        outcome_code="ULO1",
        outcome_text="Analyze web technologies and their applications",
        bloom_level="ANALYZE",
        sequence_order=1,
        created_by_id=test_user.id,
    )
    test_db.add(ulo)
    test_db.commit()
    test_db.refresh(ulo)
    return ulo


@pytest.fixture
def populated_unit(
    test_db: Session,
    test_unit: Unit,
    test_unit_outline: UnitOutline,
    test_user: User,
) -> Unit:
    """Populate a unit with topics, materials, ULOs, assessments, and accreditation data.

    Creates:
    - 3 weekly topics (weeks 1-3)
    - 3 weekly materials (weeks 1-2)
    - 2 ULOs with graduate capability mapping
    - 2 assessments (formative + summative)
    - AoL and SDG mappings
    """
    # Weekly topics — commit each individually to avoid GUID sentinel mismatch
    for week_num, title in [
        (1, "HTML Basics"),
        (2, "CSS Fundamentals"),
        (3, "JavaScript Intro"),
    ]:
        topic = WeeklyTopic(
            id=str(uuid.uuid4()),
            unit_outline_id=test_unit_outline.id,
            unit_id=test_unit.id,
            week_number=week_num,
            topic_title=title,
            created_by_id=test_user.id,
        )
        test_db.add(topic)
        test_db.commit()

    # Weekly materials
    materials_data = [
        (
            1,
            "HTML Lecture",
            "lecture",
            "<p>Introduction to HTML tags and structure.</p>",
            0,
        ),
        (1, "HTML Activity", "activity", "<p>Build your first web page.</p>", 1),
        (2, "CSS Lecture", "lecture", "<p>Styling with CSS selectors.</p>", 0),
    ]
    for week_num, title, mat_type, desc, order in materials_data:
        mat = WeeklyMaterial(
            id=str(uuid.uuid4()),
            unit_id=test_unit.id,
            week_number=week_num,
            title=title,
            type=mat_type,
            description=desc,
            order_index=order,
        )
        test_db.add(mat)
        test_db.commit()

    # ULOs
    ulo1 = UnitLearningOutcome(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        outcome_type="ulo",
        outcome_code="ULO1",
        outcome_text="Analyze web technologies and their applications",
        bloom_level="ANALYZE",
        sequence_order=1,
        created_by_id=test_user.id,
    )
    test_db.add(ulo1)
    test_db.commit()

    ulo2 = UnitLearningOutcome(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        outcome_type="ulo",
        outcome_code="ULO2",
        outcome_text="Create responsive web applications",
        bloom_level="CREATE",
        sequence_order=2,
        created_by_id=test_user.id,
    )
    test_db.add(ulo2)
    test_db.commit()

    # Graduate Capability mapping on ULO1
    gc = ULOGraduateCapabilityMapping(
        id=str(uuid.uuid4()),
        ulo_id=ulo1.id,
        capability_code="GC1",
    )
    test_db.add(gc)
    test_db.commit()

    # Assessments
    a1 = Assessment(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        title="HTML Quiz",
        type=AssessmentType.FORMATIVE.value,
        category="quiz",
        weight=20.0,
        description="Short quiz on HTML fundamentals",
        due_week=4,
        duration="30 minutes",
        submission_type="online",
        group_work=False,
    )
    test_db.add(a1)
    test_db.commit()

    a2 = Assessment(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        title="Web Project",
        type=AssessmentType.SUMMATIVE.value,
        category="project",
        weight=40.0,
        description="Build a complete website",
        due_week=12,
        submission_type="online",
        group_work=True,
        specification="<h3>Requirements</h3><p>Build a responsive site.</p>",
    )
    test_db.add(a2)
    test_db.commit()

    # AoL mapping
    aol = UnitAoLMapping(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        competency_code="AOL2",
        level="R",
        notes="Critical thinking reinforced",
    )
    test_db.add(aol)
    test_db.commit()

    # SDG mapping
    sdg = UnitSDGMapping(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        sdg_code="SDG4",
        notes="Quality Education",
    )
    test_db.add(sdg)
    test_db.commit()

    return test_unit


@pytest.fixture
def test_design(test_db: Session, test_unit: Unit) -> LearningDesign:
    """Insert a real LearningDesign row into the test database."""
    design = LearningDesign(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        version="1.0",
        status=DesignStatus.DRAFT.value,
        content={
            "topic": "Web Development Fundamentals",
            "description": "An introductory unit on web technologies",
            "objectives": [
                "Understand HTML structure",
                "Apply CSS styling",
                "Write basic JavaScript",
            ],
            "modules": [
                {"title": "HTML Basics", "weeks": [1, 2]},
                {"title": "CSS Fundamentals", "weeks": [3, 4]},
            ],
        },
    )
    test_db.add(design)
    test_db.commit()
    test_db.refresh(design)
    return design


@pytest.fixture
def test_quiz_content(
    test_db: Session, test_unit: Unit
) -> tuple[Content, list[QuizQuestion]]:
    """Insert a Content (type=quiz) with 3 QuizQuestion rows (MC, T/F, short answer)."""
    content = Content(
        id=str(uuid.uuid4()),
        title="Test Quiz",
        type=ContentType.QUIZ.value,
        unit_id=test_unit.id,
        status="draft",
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)

    q1 = QuizQuestion(
        id=str(uuid.uuid4()),
        content_id=content.id,
        question_text="What is 2+2?",
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        order_index=0,
        options=["3", "4", "5", "6"],
        correct_answers=["4"],
        answer_explanation="Basic arithmetic.",
        points=2.0,
    )
    test_db.add(q1)
    test_db.commit()

    q2 = QuizQuestion(
        id=str(uuid.uuid4()),
        content_id=content.id,
        question_text="The sky is blue.",
        question_type=QuestionType.TRUE_FALSE.value,
        order_index=1,
        options=["True", "False"],
        correct_answers=["True"],
        points=1.0,
    )
    test_db.add(q2)
    test_db.commit()

    q3 = QuizQuestion(
        id=str(uuid.uuid4()),
        content_id=content.id,
        question_text="Name the capital of Australia.",
        question_type=QuestionType.SHORT_ANSWER.value,
        order_index=2,
        correct_answers=["Canberra"],
        points=1.0,
    )
    test_db.add(q3)
    test_db.commit()

    return content, [q1, q2, q3]
