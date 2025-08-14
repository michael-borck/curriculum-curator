"""
Integration tests for database models
Tests actual database operations, not mocks
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import (
    Conversation,
    Course,
    CourseModule,
    CourseStatus,
    LRD,
    LRDStatus,
    Material,
    MaterialType,
    ModuleType,
    TaskList,
    TaskStatus,
    TeachingPhilosophy,
    User,
    UserRole,
)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = test_session_local()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User",
        role=UserRole.LECTURER.value,
        teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
        language_preference="en-AU",
        is_verified=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_course(test_db: Session, test_user: User):
    """Create a test course"""
    course = Course(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Introduction to Python",
        code="CS101",
        description="Learn Python basics",
        teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
        language_preference="en-AU",
        status=CourseStatus.PLANNING.value,
        semester="2024-S1",
        credits=3,
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


class TestUserModel:
    """Test User model functionality"""

    def test_create_user(self, test_db: Session):
        """Test creating a user"""
        user = User(
            email="newuser@example.com",
            password_hash="hashed",
            name="New User",
            role=UserRole.LECTURER.value,
        )
        test_db.add(user)
        test_db.commit()

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.teaching_philosophy == TeachingPhilosophy.MIXED_APPROACH.value
        assert user.language_preference == "en-AU"

    def test_user_relationships(
        self, test_db: Session, test_user: User, test_course: Course
    ):
        """Test user-course relationship"""
        # Refresh to load relationships
        test_db.refresh(test_user)

        assert len(test_user.courses) == 1
        assert test_user.courses[0].id == test_course.id

    def test_user_role_properties(self, test_user: User):
        """Test role checking properties"""
        assert test_user.is_lecturer is True
        assert test_user.is_admin is False
        assert test_user.is_student is False


class TestCourseModel:
    """Test Course model functionality"""

    def test_create_course(self, test_db: Session, test_user: User):
        """Test creating a course"""
        course = Course(
            user_id=test_user.id,
            title="Data Structures",
            code="CS201",
            teaching_philosophy=TeachingPhilosophy.CONSTRUCTIVIST.value,
            language_preference="en-GB",
        )
        test_db.add(course)
        test_db.commit()

        assert course.id is not None
        assert course.status == CourseStatus.PLANNING.value
        assert course.is_active is False

    def test_course_modules(self, test_db: Session, test_course: Course):
        """Test course-module relationship"""
        module1 = CourseModule(
            course_id=test_course.id,
            number=1,
            title="Week 1: Introduction",
            type=ModuleType.FLIPPED.value,
        )
        module2 = CourseModule(
            course_id=test_course.id,
            number=2,
            title="Week 2: Variables",
            type=ModuleType.TRADITIONAL.value,
        )
        test_db.add_all([module1, module2])
        test_db.commit()
        test_db.refresh(test_course)

        assert len(test_course.modules) == 2
        assert test_course.modules[0].is_flipped is True
        assert test_course.modules[1].is_flipped is False

    def test_course_progress(self, test_db: Session, test_course: Course):
        """Test course progress calculation"""
        # No modules yet
        assert test_course.progress_percentage == 0.0

        # Add modules
        module1 = CourseModule(
            course_id=test_course.id,
            number=1,
            title="Module 1",
            is_complete=True,
        )
        module2 = CourseModule(
            course_id=test_course.id,
            number=2,
            title="Module 2",
            is_complete=False,
        )
        test_db.add_all([module1, module2])
        test_db.commit()
        test_db.refresh(test_course)

        assert test_course.progress_percentage == 50.0


class TestLRDModel:
    """Test LRD model functionality"""

    def test_create_lrd(self, test_db: Session, test_course: Course):
        """Test creating an LRD"""
        lrd = LRD(
            course_id=test_course.id,
            version="1.0",
            status=LRDStatus.DRAFT.value,
            content={
                "topic": "Week 1",
                "objectives": ["Learn basics", "Understand syntax"],
                "structure": {
                    "pre_class": "Read chapter 1",
                    "in_class": "Live coding",
                    "post_class": "Practice exercises",
                },
            },
        )
        test_db.add(lrd)
        test_db.commit()

        assert lrd.id is not None
        assert lrd.status == LRDStatus.DRAFT.value
        assert "objectives" in lrd.content

    def test_lrd_task_list_relationship(self, test_db: Session, test_course: Course):
        """Test LRD-TaskList relationship"""
        lrd = LRD(
            course_id=test_course.id,
            version="1.0",
            status=LRDStatus.APPROVED.value,
            content={"topic": "Test"},
        )
        test_db.add(lrd)
        test_db.commit()

        task_list = TaskList(
            lrd_id=lrd.id,
            course_id=test_course.id,
            tasks={
                "parent_tasks": [
                    {"id": "1", "title": "Create content", "status": "pending"}
                ]
            },
            total_tasks=5,
            completed_tasks=0,
        )
        test_db.add(task_list)
        test_db.commit()
        test_db.refresh(lrd)

        assert len(lrd.task_lists) == 1
        assert lrd.task_lists[0].progress_percentage == 0.0


class TestMaterialModel:
    """Test Material model functionality"""

    def test_create_material(self, test_db: Session, test_course: Course):
        """Test creating course material"""
        material = Material(
            course_id=test_course.id,
            type=MaterialType.LECTURE.value,
            title="Introduction to Python",
            content={"slides": ["Slide 1", "Slide 2"]},
            raw_content="# Introduction\n\nWelcome to Python",
            teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
        )
        test_db.add(material)
        test_db.commit()

        assert material.id is not None
        assert material.version == 1
        assert material.is_latest is True

    def test_material_versioning(self, test_db: Session, test_course: Course):
        """Test material version tracking"""
        # Create original
        v1 = Material(
            course_id=test_course.id,
            type=MaterialType.WORKSHEET.value,
            title="Exercise 1",
            content={"questions": ["Q1", "Q2"]},
            version=1,
        )
        test_db.add(v1)
        test_db.commit()

        # Create new version
        v2 = Material(
            course_id=test_course.id,
            type=MaterialType.WORKSHEET.value,
            title="Exercise 1 (Updated)",
            content={"questions": ["Q1", "Q2", "Q3"]},
            version=2,
            parent_version_id=v1.id,
        )
        v1.is_latest = False  # Mark v1 as not latest
        test_db.add(v2)
        test_db.commit()

        test_db.refresh(v1)
        test_db.refresh(v2)

        assert v1.is_latest is False
        assert v2.is_latest is True
        assert v2.parent_version_id == v1.id
        assert len(v1.child_versions) == 1


class TestConversationModel:
    """Test Conversation model functionality"""

    def test_create_conversation(self, test_db: Session, test_course: Course):
        """Test creating a conversation history"""
        session_id = uuid.uuid4()
        conversation = Conversation(
            course_id=test_course.id,
            session_id=session_id,
            messages=[
                {"role": "user", "content": "Create a lecture"},
                {"role": "assistant", "content": "I'll help you create a lecture"},
            ],
        )
        test_db.add(conversation)
        test_db.commit()

        assert conversation.id is not None
        assert len(conversation.messages) == 2
        assert conversation.session_id == session_id


class TestTaskListModel:
    """Test TaskList model functionality"""

    def test_create_task_list(self, test_db: Session, test_course: Course):
        """Test creating a task list"""
        task_list = TaskList(
            course_id=test_course.id,
            tasks={
                "tasks": [
                    {"id": "1", "title": "Task 1", "completed": False},
                    {"id": "2", "title": "Task 2", "completed": False},
                ]
            },
            status=TaskStatus.IN_PROGRESS.value,
            total_tasks=2,
            completed_tasks=0,
        )
        test_db.add(task_list)
        test_db.commit()

        assert task_list.id is not None
        assert task_list.progress_percentage == 0.0

    def test_task_list_progress(self, test_db: Session, test_course: Course):
        """Test task list progress tracking"""
        task_list = TaskList(
            course_id=test_course.id,
            tasks={"tasks": []},
            total_tasks=4,
            completed_tasks=3,
        )
        test_db.add(task_list)
        test_db.commit()

        assert task_list.progress_percentage == 75.0

        # Complete all tasks
        task_list.completed_tasks = 4
        task_list.status = TaskStatus.COMPLETE.value
        task_list.completed_at = datetime.utcnow()
        test_db.commit()

        assert task_list.progress_percentage == 100.0
        assert task_list.completed_at is not None


class TestModelRelationships:
    """Test complex relationships between models"""

    def test_full_course_structure(self, test_db: Session, test_user: User):
        """Test creating a complete course structure"""
        # Create course
        course = Course(
            user_id=test_user.id,
            title="Complete Course",
            code="CS999",
            teaching_philosophy=test_user.teaching_philosophy,
        )
        test_db.add(course)
        test_db.commit()

        # Add LRD
        lrd = LRD(
            course_id=course.id,
            version="1.0",
            status=LRDStatus.APPROVED.value,
            content={"topic": "Full course"},
        )
        test_db.add(lrd)

        # Add modules
        module = CourseModule(
            course_id=course.id,
            number=1,
            title="Module 1",
        )
        test_db.add(module)
        test_db.commit()

        # Add material to module
        material = Material(
            course_id=course.id,
            module_id=module.id,
            type=MaterialType.LECTURE.value,
            title="Lecture 1",
            content={"content": "Lecture content"},
        )
        test_db.add(material)

        # Add conversation
        conversation = Conversation(
            course_id=course.id,
            lrd_id=lrd.id,
            session_id=uuid.uuid4(),
            messages=[{"role": "system", "content": "Starting conversation"}],
        )
        test_db.add(conversation)

        # Add task list
        task_list = TaskList(
            course_id=course.id,
            lrd_id=lrd.id,
            tasks={"tasks": []},
            total_tasks=1,
        )
        test_db.add(task_list)

        test_db.commit()
        test_db.refresh(course)

        # Verify all relationships
        assert len(course.modules) == 1
        assert len(course.lrds) == 1
        assert len(course.materials) == 1
        assert len(course.conversations) == 1
        assert len(course.task_lists) == 1
        assert course.modules[0].materials[0].id == material.id
