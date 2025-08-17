"""
Content creation workflow service for guided course development
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    AssessmentPlan,
    Content,
    ContentCategory,
    ContentType,
    CourseOutline,
    SessionStatus,
    Unit,
    UnitLearningOutcome,
    User,
    WeeklyTopic,
    WorkflowChatSession,
    WorkflowStage,
)
from app.services.llm_service import llm_service


class WorkflowDecision(str, Enum):
    """Workflow decision types"""

    UNIT_TYPE = "unit_type"
    DELIVERY_MODE = "delivery_mode"
    DURATION_WEEKS = "duration_weeks"
    ASSESSMENT_STRATEGY = "assessment_strategy"
    PEDAGOGY_APPROACH = "pedagogy_approach"
    CONTENT_DEPTH = "content_depth"
    STUDENT_LEVEL = "student_level"
    PREREQUISITES = "prerequisites"


class WorkflowQuestion:
    """Workflow question configuration"""

    def __init__(
        self,
        key: str,
        question: str,
        options: list[str] | None = None,
        input_type: str = "select",
        required: bool = True,
        depends_on: str | None = None,
        stage: WorkflowStage = WorkflowStage.INITIAL_PLANNING,
    ):
        self.key = key
        self.question = question
        self.options = options
        self.input_type = input_type  # select, text, number, multiselect
        self.required = required
        self.depends_on = depends_on
        self.stage = stage


class ContentWorkflowService:
    """Service for managing guided content creation workflows"""

    # Workflow questions by stage
    WORKFLOW_QUESTIONS = {
        WorkflowStage.INITIAL_PLANNING: [
            WorkflowQuestion(
                key="unit_type",
                question="What type of unit is this?",
                options=[
                    "Core/Foundation Unit",
                    "Elective Unit",
                    "Capstone/Project Unit",
                    "Research Methods Unit",
                    "Professional Practice Unit",
                ],
                stage=WorkflowStage.INITIAL_PLANNING,
            ),
            WorkflowQuestion(
                key="student_level",
                question="What is the target student level?",
                options=[
                    "First Year (Introductory)",
                    "Second Year (Intermediate)",
                    "Third Year (Advanced)",
                    "Postgraduate",
                    "Mixed Levels",
                ],
                stage=WorkflowStage.INITIAL_PLANNING,
            ),
            WorkflowQuestion(
                key="delivery_mode",
                question="How will this unit be delivered?",
                options=["Face-to-face", "Online", "Blended/Hybrid", "Flexible"],
                stage=WorkflowStage.INITIAL_PLANNING,
            ),
            WorkflowQuestion(
                key="duration_weeks",
                question="How many weeks will the unit run?",
                input_type="number",
                stage=WorkflowStage.INITIAL_PLANNING,
            ),
        ],
        WorkflowStage.LEARNING_DESIGN: [
            WorkflowQuestion(
                key="pedagogy_approach",
                question="What is your primary pedagogical approach?",
                options=[
                    "Flipped Classroom",
                    "Problem-Based Learning",
                    "Project-Based Learning",
                    "Traditional Lectures + Tutorials",
                    "Workshop-Based",
                    "Research-Led Teaching",
                    "Collaborative Learning",
                ],
                stage=WorkflowStage.LEARNING_DESIGN,
            ),
            WorkflowQuestion(
                key="learning_outcome_count",
                question="How many unit learning outcomes do you plan to have?",
                options=["3-4 outcomes", "5-6 outcomes", "7-8 outcomes", "More than 8"],
                stage=WorkflowStage.LEARNING_DESIGN,
            ),
            WorkflowQuestion(
                key="bloom_focus",
                question="What cognitive levels will you primarily target?",
                options=[
                    "Lower order (Remember, Understand)",
                    "Middle order (Apply, Analyze)",
                    "Higher order (Evaluate, Create)",
                    "Full spectrum (All levels)",
                ],
                stage=WorkflowStage.LEARNING_DESIGN,
            ),
        ],
        WorkflowStage.CONTENT_STRUCTURING: [
            WorkflowQuestion(
                key="content_organization",
                question="How will you organize the content?",
                options=[
                    "Topic-based (by subject matter)",
                    "Skill-based (by competencies)",
                    "Project-based (around projects)",
                    "Problem-based (around problems)",
                    "Chronological (time-based)",
                    "Thematic (by themes)",
                ],
                stage=WorkflowStage.CONTENT_STRUCTURING,
            ),
            WorkflowQuestion(
                key="weekly_pattern",
                question="What will be your typical weekly pattern?",
                options=[
                    "Lecture + Tutorial + Lab",
                    "Lecture + Workshop",
                    "Seminar + Independent Study",
                    "Online Modules + Discussion",
                    "Flexible/Varies by Week",
                ],
                stage=WorkflowStage.CONTENT_STRUCTURING,
            ),
        ],
        WorkflowStage.ASSESSMENT_PLANNING: [
            WorkflowQuestion(
                key="assessment_strategy",
                question="What is your assessment philosophy?",
                options=[
                    "Continuous assessment (many small tasks)",
                    "Major assessments (few large tasks)",
                    "Balanced mix",
                    "Portfolio-based",
                    "Exam-heavy",
                    "Project-focused",
                ],
                stage=WorkflowStage.ASSESSMENT_PLANNING,
            ),
            WorkflowQuestion(
                key="assessment_count",
                question="How many assessments will you have?",
                options=["2-3 assessments", "4-5 assessments", "6+ assessments"],
                stage=WorkflowStage.ASSESSMENT_PLANNING,
            ),
            WorkflowQuestion(
                key="formative_assessment",
                question="Will you include formative (non-graded) assessments?",
                options=["Yes, regularly", "Yes, occasionally", "No, summative only"],
                stage=WorkflowStage.ASSESSMENT_PLANNING,
            ),
        ],
    }

    def __init__(self, db: Session):
        """Initialize workflow service"""
        self.db = db

    async def create_workflow_session(
        self, unit_id: str, user_id: str, session_name: str | None = None
    ) -> WorkflowChatSession:
        """Create a new workflow session for guided content creation"""
        # Verify unit exists
        unit = self.db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == user_id).first()
        if not unit:
            raise ValueError("Unit not found or access denied")

        # Create session
        session = WorkflowChatSession(
            id=uuid.uuid4(),
            user_id=user_id,
            unit_id=unit_id,
            session_name=session_name or f"Workflow for {unit.name}",
            session_type="content_creation",
            status=SessionStatus.ACTIVE,
            current_stage=WorkflowStage.INITIAL_PLANNING,
            progress_percentage=0.0,
            message_count=0,
            total_tokens_used=0,
            decisions_made={},
            chat_history=[],
            workflow_data={
                "unit_name": unit.name,
                "unit_code": unit.code,
                "started_at": datetime.utcnow().isoformat(),
            },
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    async def get_next_question(
        self, session_id: str, user_id: str
    ) -> dict[str, Any] | None:
        """Get the next question in the workflow"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(WorkflowChatSession.id == session_id, WorkflowChatSession.user_id == user_id)
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        # Get questions for current stage
        stage_questions = self.WORKFLOW_QUESTIONS.get(session.current_stage, [])

        # Find unanswered questions
        decisions_made = session.decisions_made or {}
        for question in stage_questions:
            if question.key not in decisions_made:
                # Check dependencies
                if question.depends_on and question.depends_on not in decisions_made:
                    continue

                return {
                    "question_key": question.key,
                    "question_text": question.question,
                    "options": question.options,
                    "input_type": question.input_type,
                    "required": question.required,
                    "stage": session.current_stage,
                    "progress": session.progress_percentage,
                }

        # No more questions in this stage
        return None

    async def submit_answer(
        self, session_id: str, user_id: str, question_key: str, answer: Any
    ) -> dict[str, Any]:
        """Submit an answer to a workflow question"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(WorkflowChatSession.id == session_id, WorkflowChatSession.user_id == user_id)
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        # Record decision
        session.record_decision(question_key, answer)

        # Add to chat history
        chat_history = session.chat_history or []
        chat_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "answer",
                "question_key": question_key,
                "answer": answer,
            }
        )
        session.chat_history = chat_history
        session.message_count += 1

        # Check if stage is complete
        stage_complete = await self._is_stage_complete(session)

        if stage_complete:
            # Move to next stage
            next_stage = await self._get_next_stage(session.current_stage)
            if next_stage:
                session.advance_to_stage(next_stage)
                
                # Generate stage summary
                summary = await self._generate_stage_summary(session)
                chat_history.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "summary",
                        "stage": session.current_stage,
                        "content": summary,
                    }
                )
                session.chat_history = chat_history
            else:
                # Workflow complete
                session.mark_as_complete()

        self.db.commit()

        # Get next question or completion status
        if session.status == SessionStatus.COMPLETED:
            return {
                "status": "completed",
                "message": "Workflow completed successfully!",
                "next_steps": await self._get_completion_next_steps(session),
            }
        else:
            next_question = await self.get_next_question(session_id, user_id)
            return {
                "status": "in_progress",
                "next_question": next_question,
                "stage": session.current_stage,
                "progress": session.progress_percentage,
            }

    async def _is_stage_complete(self, session: WorkflowChatSession) -> bool:
        """Check if current stage is complete"""
        stage_questions = self.WORKFLOW_QUESTIONS.get(session.current_stage, [])
        decisions_made = session.decisions_made or {}

        for question in stage_questions:
            if question.required and question.key not in decisions_made:
                return False

        return True

    async def _get_next_stage(self, current_stage: WorkflowStage) -> WorkflowStage | None:
        """Get the next stage in the workflow"""
        stage_order = [
            WorkflowStage.INITIAL_PLANNING,
            WorkflowStage.LEARNING_DESIGN,
            WorkflowStage.CONTENT_STRUCTURING,
            WorkflowStage.ASSESSMENT_PLANNING,
            WorkflowStage.MATERIAL_GENERATION,
        ]

        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass

        return None

    async def _generate_stage_summary(self, session: WorkflowChatSession) -> str:
        """Generate a summary of decisions made in a stage"""
        decisions = session.decisions_made or {}
        stage = session.current_stage

        summary_parts = [f"## {stage.replace('_', ' ').title()} Summary\n"]

        # Add decisions for this stage
        stage_questions = self.WORKFLOW_QUESTIONS.get(stage, [])
        for question in stage_questions:
            if question.key in decisions:
                answer = decisions[question.key]["value"]
                summary_parts.append(f"- **{question.question}**: {answer}")

        return "\n".join(summary_parts)

    async def _get_completion_next_steps(self, session: WorkflowChatSession) -> list[str]:
        """Get next steps after workflow completion"""
        return [
            "1. Review the generated course structure",
            "2. Generate content for each week",
            "3. Create assessment rubrics",
            "4. Add learning resources",
            "5. Review and refine learning outcomes",
        ]

    async def generate_course_structure(
        self, session_id: str, user_id: str
    ) -> dict[str, Any]:
        """Generate course structure based on workflow decisions"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(WorkflowChatSession.id == session_id, WorkflowChatSession.user_id == user_id)
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        decisions = session.decisions_made or {}
        unit = self.db.query(Unit).filter(Unit.id == session.unit_id).first()

        # Check if structure already exists
        existing_outline = (
            self.db.query(CourseOutline).filter(CourseOutline.unit_id == session.unit_id).first()
        )

        if existing_outline:
            return {
                "status": "exists",
                "message": "Course structure already exists for this unit",
                "outline_id": str(existing_outline.id),
            }

        try:
            # Create course outline
            duration_weeks = int(decisions.get("duration_weeks", {}).get("value", 12))
            
            outline = CourseOutline(
                id=uuid.uuid4(),
                unit_id=session.unit_id,
                title=f"Course Outline: {unit.name}",
                description=await self._generate_outline_description(session, unit),
                duration_weeks=duration_weeks,
                delivery_mode=decisions.get("delivery_mode", {}).get("value"),
                teaching_pattern=decisions.get("weekly_pattern", {}).get("value"),
                created_by_id=user_id,
            )
            self.db.add(outline)
            self.db.flush()

            # Generate learning outcomes
            outcomes = await self._generate_learning_outcomes(session, unit, outline)
            for outcome_data in outcomes:
                outcome = UnitLearningOutcome(
                    id=uuid.uuid4(),
                    unit_id=session.unit_id,
                    course_outline_id=outline.id,
                    **outcome_data,
                    created_by_id=user_id,
                )
                self.db.add(outcome)

            # Generate weekly topics
            topics = await self._generate_weekly_topics(session, unit, outline)
            for topic_data in topics:
                topic = WeeklyTopic(
                    id=uuid.uuid4(),
                    unit_id=session.unit_id,
                    course_outline_id=outline.id,
                    **topic_data,
                    created_by_id=user_id,
                )
                self.db.add(topic)

            # Generate assessment plan
            assessments = await self._generate_assessments(session, unit, outline)
            for assess_data in assessments:
                assessment = AssessmentPlan(
                    id=uuid.uuid4(),
                    unit_id=session.unit_id,
                    course_outline_id=outline.id,
                    **assess_data,
                    created_by_id=user_id,
                )
                self.db.add(assessment)

            self.db.commit()

            return {
                "status": "success",
                "message": "Course structure generated successfully",
                "outline_id": str(outline.id),
                "components": {
                    "learning_outcomes": len(outcomes),
                    "weekly_topics": len(topics),
                    "assessments": len(assessments),
                },
            }

        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error generating course structure: {str(e)}")

    async def _generate_outline_description(
        self, session: WorkflowChatSession, unit: Unit
    ) -> str:
        """Generate course outline description based on decisions"""
        decisions = session.decisions_made or {}
        
        parts = [
            f"This {decisions.get('unit_type', {}).get('value', 'unit')} ",
            f"is designed for {decisions.get('student_level', {}).get('value', 'students')} ",
            f"and will be delivered via {decisions.get('delivery_mode', {}).get('value', 'flexible')} mode. ",
            f"The pedagogical approach emphasizes {decisions.get('pedagogy_approach', {}).get('value', 'active learning')} ",
            f"with {decisions.get('assessment_strategy', {}).get('value', 'balanced')} assessment strategy.",
        ]
        
        return "".join(parts)

    async def _generate_learning_outcomes(
        self, session: WorkflowChatSession, unit: Unit, outline: CourseOutline
    ) -> list[dict[str, Any]]:
        """Generate learning outcomes based on workflow decisions"""
        decisions = session.decisions_made or {}
        
        # Determine number of outcomes
        outcome_count = 5  # Default
        outcome_count_str = decisions.get("learning_outcome_count", {}).get("value", "5-6 outcomes")
        if "3-4" in outcome_count_str:
            outcome_count = 4
        elif "7-8" in outcome_count_str:
            outcome_count = 7
        elif "More than" in outcome_count_str:
            outcome_count = 9

        # Determine Bloom levels to use
        bloom_focus = decisions.get("bloom_focus", {}).get("value", "Full spectrum")
        
        if "Lower order" in bloom_focus:
            bloom_levels = ["remember", "understand"]
        elif "Middle order" in bloom_focus:
            bloom_levels = ["apply", "analyze"]
        elif "Higher order" in bloom_focus:
            bloom_levels = ["evaluate", "create"]
        else:
            bloom_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

        # Generate outcomes
        outcomes = []
        for i in range(outcome_count):
            bloom_level = bloom_levels[i % len(bloom_levels)]
            outcome_text = await self._generate_outcome_text(unit, bloom_level, i + 1)
            
            outcomes.append(
                {
                    "outcome_type": "ulo",
                    "outcome_code": f"ULO{i + 1}",
                    "outcome_text": outcome_text,
                    "bloom_level": bloom_level,
                    "sequence_order": i + 1,
                }
            )

        return outcomes

    async def _generate_outcome_text(self, unit: Unit, bloom_level: str, number: int) -> str:
        """Generate a learning outcome text"""
        # Simple template-based generation
        # In production, this would use LLM service
        
        verb_map = {
            "remember": ["identify", "list", "describe"],
            "understand": ["explain", "summarize", "classify"],
            "apply": ["apply", "demonstrate", "solve"],
            "analyze": ["analyze", "examine", "compare"],
            "evaluate": ["evaluate", "assess", "critique"],
            "create": ["create", "design", "develop"],
        }
        
        verbs = verb_map.get(bloom_level, ["demonstrate"])
        verb = verbs[number % len(verbs)]
        
        return f"Students will be able to {verb} key concepts in {unit.name}"

    async def _generate_weekly_topics(
        self, session: WorkflowChatSession, unit: Unit, outline: CourseOutline
    ) -> list[dict[str, Any]]:
        """Generate weekly topics based on workflow decisions"""
        decisions = session.decisions_made or {}
        duration_weeks = outline.duration_weeks
        
        topics = []
        for week in range(1, duration_weeks + 1):
            # Determine week type
            if week == 1:
                topic_title = "Introduction and Course Overview"
                week_type = "regular"
            elif week == duration_weeks // 2:
                topic_title = "Mid-term Review and Assessment"
                week_type = "assessment"
            elif week == duration_weeks:
                topic_title = "Course Review and Final Assessment"
                week_type = "assessment"
            elif week == duration_weeks - 1:
                topic_title = "Revision and Exam Preparation"
                week_type = "revision"
            else:
                topic_title = f"Week {week} Topic"
                week_type = "regular"

            topics.append(
                {
                    "week_number": week,
                    "week_type": week_type,
                    "topic_title": topic_title,
                    "topic_description": f"Content for week {week}",
                    "learning_objectives": f"Objectives for week {week}",
                }
            )

        return topics

    async def _generate_assessments(
        self, session: WorkflowChatSession, unit: Unit, outline: CourseOutline
    ) -> list[dict[str, Any]]:
        """Generate assessment plan based on workflow decisions"""
        decisions = session.decisions_made or {}
        
        # Determine number of assessments
        assessment_count = 3  # Default
        count_str = decisions.get("assessment_count", {}).get("value", "2-3 assessments")
        if "4-5" in count_str:
            assessment_count = 4
        elif "6+" in count_str:
            assessment_count = 6

        # Determine assessment types based on strategy
        strategy = decisions.get("assessment_strategy", {}).get("value", "Balanced mix")
        
        if "Continuous" in strategy:
            types = ["quiz", "assignment", "participation", "quiz", "assignment"]
            weights = [10, 20, 10, 10, 20]
        elif "Major" in strategy:
            types = ["assignment", "project", "exam"]
            weights = [30, 40, 30]
        elif "Portfolio" in strategy:
            types = ["portfolio", "presentation", "reflection"]
            weights = [50, 30, 20]
        elif "Exam" in strategy:
            types = ["quiz", "exam", "exam"]
            weights = [20, 40, 40]
        else:  # Balanced
            types = ["assignment", "quiz", "project", "exam"]
            weights = [25, 15, 35, 25]

        # Generate assessments
        assessments = []
        total_weight = sum(weights[:assessment_count])
        
        for i in range(assessment_count):
            assessment_type = types[i % len(types)]
            weight = weights[i % len(weights)] * 100 / total_weight  # Normalize to 100%
            
            assessments.append(
                {
                    "assessment_name": f"Assessment {i + 1}: {assessment_type.title()}",
                    "assessment_type": assessment_type,
                    "assessment_mode": "summative",
                    "description": f"Assessment task {i + 1}",
                    "weight_percentage": round(weight, 1),
                    "due_week": min((i + 1) * (outline.duration_weeks // assessment_count), outline.duration_weeks),
                }
            )

        return assessments

    async def get_workflow_status(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Get current workflow status and progress"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(WorkflowChatSession.id == session_id, WorkflowChatSession.user_id == user_id)
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        return {
            "session_id": str(session.id),
            "status": session.status,
            "current_stage": session.current_stage,
            "progress_percentage": session.progress_percentage,
            "decisions_made": session.decisions_made,
            "message_count": session.message_count,
            "can_generate_structure": session.status == SessionStatus.COMPLETED,
            "duration_minutes": session.total_duration_minutes,
        }

    async def get_stage_questions(self, stage: WorkflowStage) -> list[dict[str, Any]]:
        """Get all questions for a specific stage"""
        questions = self.WORKFLOW_QUESTIONS.get(stage, [])
        
        return [
            {
                "key": q.key,
                "question": q.question,
                "options": q.options,
                "input_type": q.input_type,
                "required": q.required,
                "depends_on": q.depends_on,
            }
            for q in questions
        ]