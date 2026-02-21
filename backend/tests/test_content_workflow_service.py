"""
Tests for Content Workflow service using in-memory SQLite.
LLM calls are mocked; all other DB interactions use real in-memory SQLite.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models import SessionStatus, Unit, UnitOutline, User, WorkflowStage
from app.models.chat_session import WorkflowChatSession
from app.services.content_workflow_service import ContentWorkflowService


# ─── GET STAGE QUESTIONS ──────────────────────────────────────


class TestGetStageQuestions:
    @pytest.mark.asyncio
    async def test_course_overview_questions(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        questions = await svc.get_stage_questions(WorkflowStage.COURSE_OVERVIEW)

        assert len(questions) > 0
        keys = [q["key"] for q in questions]
        assert "unit_type" in keys
        assert "student_level" in keys
        assert "delivery_mode" in keys

    @pytest.mark.asyncio
    async def test_learning_outcomes_questions(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        questions = await svc.get_stage_questions(WorkflowStage.LEARNING_OUTCOMES)

        keys = [q["key"] for q in questions]
        assert "pedagogy_approach" in keys

    @pytest.mark.asyncio
    async def test_unknown_stage_returns_empty(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        questions = await svc.get_stage_questions(WorkflowStage.COMPLETED)
        assert questions == []


# ─── CREATE WORKFLOW SESSION ──────────────────────────────────


class TestCreateWorkflowSession:
    @pytest.mark.asyncio
    async def test_create_session(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id,
            user_id=test_user.id,
            session_name="Test Workflow",
        )

        assert session.user_id == test_user.id
        assert session.unit_id == test_unit.id
        assert session.session_name == "Test Workflow"
        assert session.current_stage == WorkflowStage.COURSE_OVERVIEW.value
        assert session.status == SessionStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_create_session_auto_fills_duration(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        # duration_weeks should be auto-filled from the unit
        decisions = session.decisions_made or {}
        assert "duration_weeks" in decisions

    @pytest.mark.asyncio
    async def test_create_session_unit_not_found(
        self, test_db: Session, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        with pytest.raises(ValueError, match="not found"):
            await svc.create_workflow_session(
                unit_id=str(uuid.uuid4()), user_id=test_user.id
            )


# ─── GET NEXT QUESTION ──────────────────────────────────────


class TestGetNextQuestion:
    @pytest.mark.asyncio
    async def test_get_first_question(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        question = await svc.get_next_question(str(session.id), test_user.id)
        assert question is not None
        assert "question_key" in question
        assert "options" in question

    @pytest.mark.asyncio
    async def test_session_not_found(self, test_db: Session, test_user: User):
        svc = ContentWorkflowService(test_db)
        with pytest.raises(ValueError, match="not found"):
            await svc.get_next_question(str(uuid.uuid4()), test_user.id)


# ─── SUBMIT ANSWER ──────────────────────────────────────────


class TestSubmitAnswer:
    @pytest.mark.asyncio
    async def test_submit_answer_progresses(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        # Get the first question and answer it
        question = await svc.get_next_question(str(session.id), test_user.id)
        assert question is not None

        result = await svc.submit_answer(
            str(session.id), test_user.id, question["question_key"], "Test Answer"
        )
        assert result["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_submit_all_answers_reaches_ready(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        # Answer all questions until completion
        max_questions = 20  # safety limit
        for _ in range(max_questions):
            question = await svc.get_next_question(str(session.id), test_user.id)
            if question is None:
                # Stage complete, but submit_answer handles advancement
                break

            result = await svc.submit_answer(
                str(session.id),
                test_user.id,
                question["question_key"],
                question["options"][0] if question["options"] else "Answer",
            )

            if result["status"] == "ready_to_generate":
                break
        else:
            pytest.fail("Workflow did not complete within max_questions")

        assert result["status"] == "ready_to_generate"

    @pytest.mark.asyncio
    async def test_submit_answer_session_not_found(
        self, test_db: Session, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        with pytest.raises(ValueError, match="not found"):
            await svc.submit_answer(str(uuid.uuid4()), test_user.id, "key", "value")


# ─── RESET SESSION ───────────────────────────────────────────


class TestResetSession:
    @pytest.mark.asyncio
    async def test_reset(self, test_db: Session, test_unit: Unit, test_user: User):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        # Answer a question first
        question = await svc.get_next_question(str(session.id), test_user.id)
        if question:
            await svc.submit_answer(
                str(session.id), test_user.id, question["question_key"], "Answer"
            )

        result = await svc.reset_session(str(session.id))
        assert result["status"] == "reset"
        assert result["next_question"] is not None

        # Verify session state was reset
        test_db.refresh(session)
        assert session.current_stage == WorkflowStage.COURSE_OVERVIEW.value
        assert session.progress_percentage == 0.0
        assert session.message_count == 0

    @pytest.mark.asyncio
    async def test_reset_nonexistent(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        with pytest.raises(ValueError, match="not found"):
            await svc.reset_session(str(uuid.uuid4()))


# ─── WORKFLOW STATUS ─────────────────────────────────────────


class TestWorkflowStatus:
    @pytest.mark.asyncio
    async def test_get_status(self, test_db: Session, test_unit: Unit, test_user: User):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        status = await svc.get_workflow_status(str(session.id), test_user.id)
        assert status["session_id"] == str(session.id)
        assert status["status"] == SessionStatus.ACTIVE.value
        assert status["progress"] == 0.0
        assert isinstance(status["can_generate_structure"], bool)

    @pytest.mark.asyncio
    async def test_status_not_found(self, test_db: Session, test_user: User):
        svc = ContentWorkflowService(test_db)
        with pytest.raises(ValueError, match="not found"):
            await svc.get_workflow_status(str(uuid.uuid4()), test_user.id)


# ─── CAN GENERATE STRUCTURE ─────────────────────────────────


class TestCanGenerateStructure:
    @pytest.mark.asyncio
    async def test_cannot_generate_without_answers(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        can_gen = await svc._can_generate_structure(session)
        assert can_gen is False


# ─── GENERATE EMPTY STRUCTURE ────────────────────────────────


class TestGenerateEmptyStructure:
    @pytest.mark.asyncio
    async def test_empty_structure(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        decisions = {"assessment_count": {"value": "4-5 assessments"}}
        structure = await svc._generate_empty_structure(session, test_unit, decisions)

        assert "learning_outcomes" in structure
        assert "weekly_topics" in structure
        assert "assessments" in structure
        assert len(structure["weekly_topics"]) == 12  # Unit has 12 weeks
        assert len(structure["assessments"]) == 4


# ─── FALLBACK STRUCTURE ──────────────────────────────────────


class TestFallbackMethods:
    def test_generate_sample_clos(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        context = {
            "unit_name": "Test Unit",
            "pedagogy_approach": "Problem-Based Learning",
        }
        clos = svc._generate_sample_clos(context)
        assert len(clos) == 5
        assert all("bloom_level" in c for c in clos)

    def test_generate_weekly_topics(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        context = {
            "delivery_mode": "Blended/Hybrid",
            "weekly_structure": "Lecture + Tutorial",
        }
        topics = svc._generate_weekly_topics(12, context)
        assert len(topics) == 12
        assert topics[0]["week"] == 1
        assert topics[-1]["week"] == 12

    def test_generate_assessment_plan_small(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        context = {"assessment_count": "2-3 assessments"}
        assessments = svc._generate_assessment_plan(context)
        assert len(assessments) == 3

    def test_generate_assessment_plan_medium(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        context = {"assessment_count": "4-5 assessments"}
        assessments = svc._generate_assessment_plan(context)
        assert len(assessments) == 5

    def test_generate_assessment_plan_large(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        context = {"assessment_count": "6+ assessments"}
        assessments = svc._generate_assessment_plan(context)
        assert len(assessments) == 6

    def test_generate_teaching_activities(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        context = {
            "weekly_structure": "Lecture + Tutorial",
            "delivery_mode": "Blended/Hybrid",
        }
        activities = svc._generate_teaching_activities(context)
        assert len(activities["lectures"]) > 0
        assert len(activities["tutorials"]) > 0
        assert len(activities["online"]) > 0


# ─── GENERATE UNIT STRUCTURE ─────────────────────────────────


class TestGenerateUnitStructure:
    @pytest.mark.asyncio
    async def test_generate_raises_without_enough_answers(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        with pytest.raises(ValueError, match="Not enough information"):
            await svc.generate_unit_structure(str(session.id), test_user.id)

    @pytest.mark.asyncio
    async def test_generate_returns_exists_if_outline_exists(
        self,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
        test_unit_outline: UnitOutline,
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        # Answer all required questions
        for _ in range(20):
            question = await svc.get_next_question(str(session.id), test_user.id)
            if not question:
                break
            result = await svc.submit_answer(
                str(session.id),
                test_user.id,
                question["question_key"],
                question["options"][0] if question["options"] else "Answer",
            )
            if result.get("status") == "ready_to_generate":
                break

        result = await svc.generate_unit_structure(
            str(session.id), test_user.id, use_ai=False
        )
        assert result["status"] == "exists"


# ─── STAGE SUMMARY ───────────────────────────────────────────


class TestStageSummary:
    @pytest.mark.asyncio
    async def test_generate_stage_summary(
        self, test_db: Session, test_unit: Unit, test_user: User
    ):
        svc = ContentWorkflowService(test_db)
        session = await svc.create_workflow_session(
            unit_id=test_unit.id, user_id=test_user.id
        )

        summary = await svc._generate_stage_summary(session)
        assert "Stage" in summary


# ─── NEXT STAGE LOGIC ────────────────────────────────────────


class TestNextStage:
    def test_course_overview_to_learning_outcomes(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        result = svc._get_next_stage(WorkflowStage.COURSE_OVERVIEW)
        assert result == WorkflowStage.LEARNING_OUTCOMES

    def test_learning_outcomes_to_unit_breakdown(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        result = svc._get_next_stage(WorkflowStage.LEARNING_OUTCOMES)
        assert result == WorkflowStage.UNIT_BREAKDOWN

    def test_unit_breakdown_to_weekly_planning(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        result = svc._get_next_stage(WorkflowStage.UNIT_BREAKDOWN)
        assert result == WorkflowStage.WEEKLY_PLANNING

    def test_weekly_planning_to_completed(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        result = svc._get_next_stage(WorkflowStage.WEEKLY_PLANNING)
        assert result == WorkflowStage.COMPLETED

    def test_completed_returns_none(self, test_db: Session):
        svc = ContentWorkflowService(test_db)
        result = svc._get_next_stage(WorkflowStage.COMPLETED)
        assert result is None
