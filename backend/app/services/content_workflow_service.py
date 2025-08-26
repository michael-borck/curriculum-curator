"""
Refactored Content Workflow Service for guided content creation
Clean architecture with proper method calls and error handling
"""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from app.models import SessionStatus, Unit, User, WorkflowChatSession, WorkflowStage
from app.models.unit_outline import UnitOutline
from app.schemas.llm_generation import (
    AssessmentStrategy,
    PedagogyApproach,
    UnitStructureContext,
    UnitStructureResponse,
    get_json_schema_for_prompt,
)
from app.services.llm_service import llm_service
from app.services.prompt_templates import prepare_unit_structure_prompt
from app.services.workflow_structure_creator import WorkflowStructureCreator


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
        stage: WorkflowStage = WorkflowStage.COURSE_OVERVIEW,
    ):
        self.key = key
        self.question = question
        self.options = options
        self.input_type = input_type
        self.required = required
        self.depends_on = depends_on
        self.stage = stage


class ContentWorkflowService:
    """Service for managing content creation workflow"""

    # Define workflow questions for each stage
    WORKFLOW_QUESTIONS: ClassVar[dict] = {
        WorkflowStage.COURSE_OVERVIEW: [
            WorkflowQuestion(
                key="unit_type",
                question="What type of unit is this?",
                options=[
                    "Theoretical/Conceptual",
                    "Practical/Applied",
                    "Mixed Theory & Practice",
                    "Project-Based",
                    "Research Methods Unit",
                    "Professional Practice Unit",
                ],
                stage=WorkflowStage.COURSE_OVERVIEW,
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
                stage=WorkflowStage.COURSE_OVERVIEW,
            ),
            WorkflowQuestion(
                key="delivery_mode",
                question="How will this unit be delivered?",
                options=["Face-to-face", "Online", "Blended/Hybrid", "Flexible"],
                stage=WorkflowStage.COURSE_OVERVIEW,
            ),
            # Note: duration_weeks is removed as it comes from the unit
        ],
        WorkflowStage.LEARNING_OUTCOMES: [
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
                stage=WorkflowStage.LEARNING_OUTCOMES,
            ),
            WorkflowQuestion(
                key="num_learning_outcomes",
                question="How many course learning outcomes will you have?",
                options=["3-4 CLOs", "5-6 CLOs", "7-8 CLOs"],
                stage=WorkflowStage.LEARNING_OUTCOMES,
            ),
            WorkflowQuestion(
                key="outcome_focus",
                question="What is the primary focus of learning outcomes?",
                options=[
                    "Knowledge & Understanding",
                    "Skills & Application",
                    "Critical Thinking & Analysis",
                    "Professional Competencies",
                    "Research & Innovation",
                    "Balanced Mix",
                ],
                stage=WorkflowStage.LEARNING_OUTCOMES,
            ),
        ],
        WorkflowStage.UNIT_BREAKDOWN: [
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
                stage=WorkflowStage.UNIT_BREAKDOWN,
            ),
            WorkflowQuestion(
                key="assessment_count",
                question="How many assessments will you have?",
                options=["2-3 assessments", "4-5 assessments", "6+ assessments"],
                stage=WorkflowStage.UNIT_BREAKDOWN,
            ),
            WorkflowQuestion(
                key="formative_assessment",
                question="Will you include formative (non-graded) assessments?",
                options=["Yes, regularly", "Yes, occasionally", "No, summative only"],
                stage=WorkflowStage.UNIT_BREAKDOWN,
            ),
        ],
        WorkflowStage.WEEKLY_PLANNING: [
            WorkflowQuestion(
                key="weekly_structure",
                question="What's your typical weekly structure?",
                options=[
                    "Lecture + Tutorial",
                    "Lecture + Lab/Workshop",
                    "Workshop Only",
                    "Seminar + Independent Study",
                    "Online Modules + Discussion",
                    "Flexible/Varies by Week",
                ],
                stage=WorkflowStage.WEEKLY_PLANNING,
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
        # Find the unit
        unit = (
            self.db.query(Unit)
            .filter(Unit.id == unit_id, Unit.owner_id == user_id)
            .first()
        )

        if not unit:
            raise ValueError("Unit not found or access denied")

        # Create session with proper initial state
        session = WorkflowChatSession(
            id=uuid.uuid4(),
            user_id=user_id,
            unit_id=unit_id,
            session_name=session_name or f"Workflow for {unit.title}",
            session_type="content_creation",
            status=SessionStatus.ACTIVE,
            current_stage=WorkflowStage.COURSE_OVERVIEW,
            progress_percentage=0.0,
            message_count=0,
            total_tokens_used=0,
            decisions_made={},
            messages=[],
            workflow_data={
                "unit_name": unit.title,
                "unit_code": unit.code,
                # Store unit duration to skip redundant question
                "duration_weeks": getattr(unit, "duration_weeks", None)
                or getattr(unit, "weeks", 12),
                "started_at": datetime.utcnow().isoformat(),
            },
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Auto-fill duration_weeks decision immediately
        if session.workflow_data.get("duration_weeks"):
            session.add_decision(
                "duration_weeks", session.workflow_data["duration_weeks"]
            )
            self.db.commit()

        return session

    async def get_next_question(
        self, session_id: str, user_id: str
    ) -> dict[str, Any] | None:
        """Get the next unanswered question in the workflow"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(
                WorkflowChatSession.id == session_id,
                WorkflowChatSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        # Get questions for current stage
        stage_questions = self.WORKFLOW_QUESTIONS.get(session.current_stage, [])
        decisions_made = session.decisions_made or {}

        # Find first unanswered question
        for question in stage_questions:
            # Check if already answered
            if question.key in decisions_made:
                continue

            # Check dependencies
            if question.depends_on and question.depends_on not in decisions_made:
                continue

            # Return the question
            return {
                "question_key": question.key,
                "question_text": question.question,
                "options": question.options,
                "input_type": question.input_type,
                "required": question.required,
                "stage": session.current_stage,
                "progress": session.progress_percentage,
            }

        # No more questions in current stage
        return None

    async def submit_answer(
        self, session_id: str, user_id: str, question_key: str, answer: Any
    ) -> dict[str, Any]:
        """Submit an answer to a workflow question"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(
                WorkflowChatSession.id == session_id,
                WorkflowChatSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        # Record the decision
        session.add_decision(question_key, answer)

        # Add to message history
        session.add_message(
            role="user",
            content=f"Answer to '{question_key}': {answer}",
            metadata={"question_key": question_key, "stage": session.current_stage},
        )

        # Check if current stage is complete
        if await self._is_stage_complete(session):
            # Advance to next stage
            next_stage = self._get_next_stage(session.current_stage)

            if next_stage and next_stage != WorkflowStage.COMPLETED:
                session.advance_stage()
                self.db.commit()

                # Get next question from new stage
                next_question = await self.get_next_question(session_id, user_id)

                return {
                    "status": "in_progress",
                    "next_question": next_question,
                    "stage": session.current_stage,
                    "progress": session.progress_percentage,
                }
            if next_stage == WorkflowStage.COMPLETED:
                # Questions complete, ready to generate structure
                session.current_stage = WorkflowStage.COMPLETED
                session.progress_percentage = 100
                self.db.commit()

                return {
                    "status": "ready_to_generate",
                    "message": "All questions completed! Choose how to create your unit structure.",
                    "progress": 100,
                    "generation_options": {
                        "ai_assisted": "Generate structure with AI recommendations",
                        "empty_structure": "Create empty structure to fill manually",
                    },
                    "next_steps": [
                        "Review your answers",
                        "Choose generation method",
                        "Generate unit structure",
                    ],
                }
            # No more stages, ready to generate
            return {
                "status": "ready_to_generate",
                "message": "All questions answered. Ready to generate unit structure.",
                "stage": session.current_stage,
                "progress": session.progress_percentage,
                "next_steps": ["Review your answers", "Generate unit structure"],
            }
        # Stage not complete, get next question
        self.db.commit()
        next_question = await self.get_next_question(session_id, user_id)

        return {
            "status": "in_progress",
            "next_question": next_question,
            "stage": session.current_stage,
            "progress": session.progress_percentage,
        }

    async def _is_stage_complete(self, session: WorkflowChatSession) -> bool:
        """Check if all required questions in current stage are answered"""
        stage_questions = self.WORKFLOW_QUESTIONS.get(session.current_stage, [])
        decisions_made = session.decisions_made or {}

        for question in stage_questions:
            if question.required and question.key not in decisions_made:
                return False

        return True

    def _get_next_stage(self, current_stage: WorkflowStage) -> WorkflowStage | None:
        """Get the next stage in the workflow sequence"""
        # Only collect questions up to WEEKLY_PLANNING
        # CONTENT_GENERATION and QUALITY_REVIEW are for the actual generation process
        question_stages = [
            WorkflowStage.COURSE_OVERVIEW,
            WorkflowStage.LEARNING_OUTCOMES,
            WorkflowStage.UNIT_BREAKDOWN,
            WorkflowStage.WEEKLY_PLANNING,
        ]

        try:
            current_index = question_stages.index(current_stage)
            if current_index < len(question_stages) - 1:
                return question_stages[current_index + 1]
            # After WEEKLY_PLANNING, we're done with questions
            if current_stage == WorkflowStage.WEEKLY_PLANNING:
                return WorkflowStage.COMPLETED  # Ready to generate structure
        except ValueError:
            pass

        return None

    async def reset_session(self, session_id: str) -> dict[str, Any]:
        """Reset a workflow session to start over"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(WorkflowChatSession.id == session_id)
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        # Reset session state
        session.current_stage = WorkflowStage.COURSE_OVERVIEW
        session.decisions_made = {}
        session.messages = []
        session.message_count = 0
        session.progress_percentage = 0.0
        session.stages_completed = []
        session.status = SessionStatus.ACTIVE

        # Re-add duration_weeks if available
        if session.workflow_data.get("duration_weeks"):
            session.add_decision(
                "duration_weeks", session.workflow_data["duration_weeks"]
            )

        self.db.commit()

        # Get first question
        first_question = await self.get_next_question(session_id, session.user_id)

        return {
            "status": "reset",
            "message": "Session reset successfully",
            "next_question": first_question,
        }

    async def get_workflow_status(
        self, session_id: str, user_id: str
    ) -> dict[str, Any]:
        """Get current workflow status"""
        session = (
            self.db.query(WorkflowChatSession)
            .filter(
                WorkflowChatSession.id == session_id,
                WorkflowChatSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        return {
            "session_id": str(session.id),
            "status": session.status,
            "current_stage": session.current_stage,
            "progress": session.progress_percentage,
            "decisions_made": len(session.decisions_made or {}),
            "can_generate_structure": await self._can_generate_structure(session),
        }

    async def _can_generate_structure(self, session: WorkflowChatSession) -> bool:
        """Check if enough information is collected to generate structure"""
        # At minimum, need to complete COURSE_OVERVIEW and LEARNING_OUTCOMES
        required_stages = [
            WorkflowStage.COURSE_OVERVIEW,
            WorkflowStage.LEARNING_OUTCOMES,
        ]

        for stage in required_stages:
            # Check if all questions in this stage are answered
            stage_questions = self.WORKFLOW_QUESTIONS.get(stage, [])
            decisions_made = session.decisions_made or {}

            for question in stage_questions:
                if question.required and question.key not in decisions_made:
                    return False

        return True

    async def generate_unit_structure(
        self, session_id: str, user_id: str, use_ai: bool = True
    ) -> dict[str, Any]:
        """
        Generate unit structure based on workflow decisions

        Args:
            session_id: The workflow session ID
            user_id: The user ID
            use_ai: If True, use AI to generate suggestions; if False, create empty structure
        """
        session = (
            self.db.query(WorkflowChatSession)
            .filter(
                WorkflowChatSession.id == session_id,
                WorkflowChatSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            raise ValueError("Session not found")

        if not await self._can_generate_structure(session):
            raise ValueError("Not enough information to generate structure")

        # Get context from decisions
        decisions = session.decisions_made or {}
        unit = self.db.query(Unit).filter(Unit.id == session.unit_id).first()

        if not unit:
            raise ValueError("Unit not found")

        # Check if unit already has an outline
        existing_outline = (
            self.db.query(UnitOutline).filter(UnitOutline.unit_id == unit.id).first()
        )

        if existing_outline:
            return {
                "status": "exists",
                "message": "Unit already has a structure. Navigate to Unit Structure to edit it.",
                "outlineId": str(existing_outline.id),
            }

        if use_ai:
            # Generate AI-assisted structure with suggestions
            structure = await self._generate_ai_structure(session, unit, decisions)
            message = "AI-assisted unit structure generated with recommendations"
        else:
            # Generate empty structure for manual completion
            structure = await self._generate_empty_structure(session, unit, decisions)
            message = "Empty unit structure created for manual completion"

        # Use WorkflowStructureCreator to create actual database records
        creator = WorkflowStructureCreator(self.db)
        result = creator.create_unit_structure(
            session=session, unit=unit, structure_data=structure, use_ai=use_ai
        )

        # Mark session as complete
        session.mark_completed()
        self.db.commit()

        return {
            "status": "success",
            "message": message,
            "use_ai": use_ai,
            "outlineId": result["outlineId"],
            "components": result["components"],
            "structure": structure,
        }

    async def _generate_ai_structure(
        self, session: WorkflowChatSession, unit: Unit, decisions: dict
    ) -> dict[str, Any]:
        """Generate AI-assisted structure with recommendations"""
        # Map decisions to structured context
        pedagogy_map = {
            "Flipped Classroom": PedagogyApproach.FLIPPED,
            "Problem-Based Learning": PedagogyApproach.PROBLEM_BASED,
            "Project-Based Learning": PedagogyApproach.PROJECT_BASED,
            "Traditional Lectures + Tutorials": PedagogyApproach.TRADITIONAL,
            "Workshop-Based": PedagogyApproach.COLLABORATIVE,
            "Research-Led Teaching": PedagogyApproach.INQUIRY_BASED,
            "Collaborative Learning": PedagogyApproach.COLLABORATIVE,
        }

        assessment_map = {
            "Continuous assessment (many small tasks)": AssessmentStrategy.CONTINUOUS,
            "Major assessments (few large tasks)": AssessmentStrategy.MAJOR,
            "Balanced mix": AssessmentStrategy.BALANCED,
            "Portfolio-based": AssessmentStrategy.PORTFOLIO,
            "Exam-heavy": AssessmentStrategy.EXAM_HEAVY,
            "Project-focused": AssessmentStrategy.PROJECT_FOCUSED,
        }

        # Extract decisions with proper typing
        pedagogy_value = decisions.get("pedagogy_approach", {}).get(
            "value", "Problem-Based Learning"
        )
        assessment_value = decisions.get("assessment_strategy", {}).get(
            "value", "Balanced mix"
        )

        # Build context for LLM
        context = UnitStructureContext(
            unit_name=unit.title,
            unit_code=unit.code,
            unit_description=unit.description,
            duration_weeks=session.workflow_data.get("duration_weeks", 12),
            unit_type=decisions.get("unit_type", {}).get(
                "value", "Mixed Theory & Practice"
            ),
            student_level=decisions.get("student_level", {}).get(
                "value", "Second Year (Intermediate)"
            ),
            delivery_mode=decisions.get("delivery_mode", {}).get(
                "value", "Blended/Hybrid"
            ),
            pedagogy_approach=pedagogy_map.get(
                pedagogy_value, PedagogyApproach.TRADITIONAL
            ),
            weekly_structure=decisions.get("weekly_structure", {}).get(
                "value", "Lecture + Tutorial"
            ),
            num_learning_outcomes=decisions.get("num_learning_outcomes", {}).get(
                "value", "5-6 CLOs"
            ),
            outcome_focus=decisions.get("outcome_focus", {}).get(
                "value", "Balanced Mix"
            ),
            assessment_strategy=assessment_map.get(
                assessment_value, AssessmentStrategy.BALANCED
            ),
            assessment_count=decisions.get("assessment_count", {}).get(
                "value", "4-5 assessments"
            ),
            include_formative="Yes"
            in decisions.get("formative_assessment", {}).get("value", "No"),
        )

        # Get JSON schema for the response
        json_schema = get_json_schema_for_prompt(UnitStructureResponse)

        # Prepare the prompt
        prompt = prepare_unit_structure_prompt(
            context=context.model_dump(),
            json_schema=json_schema,
        )

        # Try to generate with LLM
        try:
            # Get user from session for API key preferences
            user = self.db.query(User).filter(User.id == session.user_id).first()

            # Generate structured content
            result, error = await llm_service.generate_structured_content(
                prompt=prompt,
                response_model=UnitStructureResponse,
                user=user,
                db=self.db,
                temperature=0.7,
                max_retries=3,
            )

            if result and not error:
                # Convert Pydantic model to dict for database storage
                return self._convert_llm_response_to_structure(
                    result, context.duration_weeks
                )
            # Log error and fall back to template
            print(f"LLM generation failed: {error}")
            return self._generate_fallback_structure(context)

        except Exception as e:
            # If LLM fails, use fallback template generation
            print(f"LLM generation error: {e!s}")
            return self._generate_fallback_structure(context)

    def _convert_llm_response_to_structure(
        self, response: UnitStructureResponse, duration_weeks: int
    ) -> dict[str, Any]:
        """Convert LLM response to database structure format"""
        return {
            "learning_outcomes": [
                {
                    "description": lo.description,
                    "bloom_level": lo.bloom_level.value,
                }
                for lo in response.learning_outcomes
            ],
            "weekly_topics": [
                {
                    "week": topic.week,
                    "topic": topic.topic,
                    "description": topic.description,
                    "activities": topic.activities,
                }
                for topic in response.weekly_topics[
                    :duration_weeks
                ]  # Ensure we don't exceed duration
            ],
            "assessments": [
                {
                    "name": assessment.name,
                    "type": assessment.type,
                    "weight": f"{assessment.weight}%",
                    "due_week": assessment.due_week,
                }
                for assessment in response.assessments
            ],
            "teaching_activities": {
                "lectures": [],
                "tutorials": [],
                "labs": [],
                "online": [],
            },
        }

    def _generate_fallback_structure(
        self, context: UnitStructureContext
    ) -> dict[str, Any]:
        """Generate fallback structure when LLM is unavailable"""
        # Use the existing template methods as fallback
        return {
            "learning_outcomes": self._generate_sample_clos(context.model_dump()),
            "weekly_topics": self._generate_weekly_topics(
                context.duration_weeks, context.model_dump()
            ),
            "assessments": self._generate_assessment_plan(context.model_dump()),
            "teaching_activities": self._generate_teaching_activities(
                context.model_dump()
            ),
        }

    async def _generate_empty_structure(
        self, session: WorkflowChatSession, unit: Unit, decisions: dict
    ) -> dict[str, Any]:
        """Generate empty structure for manual completion"""
        num_weeks = int(session.workflow_data.get("duration_weeks", 12))

        # Extract assessment count
        assessment_count_str = decisions.get("assessment_count", {}).get(
            "value", "4-5 assessments"
        )
        if "2-3" in assessment_count_str:
            num_assessments = 3
        elif "4-5" in assessment_count_str:
            num_assessments = 4
        else:
            num_assessments = 6

        return {
            "learning_outcomes": [
                {"id": i, "description": "", "bloom_level": ""} for i in range(1, 6)
            ],
            "weekly_topics": [
                {"week": i, "topic": "", "description": "", "activities": []}
                for i in range(1, num_weeks + 1)
            ],
            "assessments": [
                {"id": i, "name": "", "type": "", "weight": "", "due_week": ""}
                for i in range(1, num_assessments + 1)
            ],
            "teaching_activities": {
                "lectures": [],
                "tutorials": [],
                "labs": [],
                "online": [],
            },
        }

    def _generate_sample_clos(self, context: dict) -> list[dict]:
        """Generate sample CLOs based on context (for AI-assisted)"""
        # This is a placeholder - real implementation would use LLM
        return [
            {
                "id": 1,
                "description": f"Understand fundamental concepts of {context['unit_name']}",
                "bloom_level": "Understanding",
            },
            {
                "id": 2,
                "description": f"Apply {context['pedagogy_approach'].lower()} techniques to solve problems",
                "bloom_level": "Applying",
            },
            {
                "id": 3,
                "description": "Analyze complex scenarios and propose solutions",
                "bloom_level": "Analyzing",
            },
            {
                "id": 4,
                "description": "Evaluate different approaches and methodologies",
                "bloom_level": "Evaluating",
            },
            {
                "id": 5,
                "description": "Create original solutions to domain-specific challenges",
                "bloom_level": "Creating",
            },
        ]

    def _generate_weekly_topics(self, num_weeks: int, context: dict) -> list[dict]:
        """Generate weekly topic suggestions (for AI-assisted)"""
        # This is a placeholder - real implementation would use LLM
        topics = []
        for week in range(1, num_weeks + 1):
            if week == 1:
                topic = "Introduction and Course Overview"
            elif week == num_weeks:
                topic = "Review and Exam Preparation"
            elif week == num_weeks // 2:
                topic = "Mid-semester Review and Integration"
            else:
                topic = f"Module {week - 1}: Topic to be defined"

            topics.append(
                {
                    "week": week,
                    "topic": topic,
                    "description": f"Week {week} content for {context['delivery_mode']} delivery",
                    "activities": [context["weekly_structure"]],
                }
            )
        return topics

    def _generate_assessment_plan(self, context: dict) -> list[dict]:
        """Generate assessment suggestions (for AI-assisted)"""
        # This is a placeholder - real implementation would use LLM
        assessments = []

        if "2-3" in context["assessment_count"]:
            assessments = [
                {
                    "id": 1,
                    "name": "Assignment 1",
                    "type": "Individual Assignment",
                    "weight": "30%",
                    "due_week": 5,
                },
                {
                    "id": 2,
                    "name": "Group Project",
                    "type": "Group Work",
                    "weight": "30%",
                    "due_week": 10,
                },
                {
                    "id": 3,
                    "name": "Final Exam",
                    "type": "Examination",
                    "weight": "40%",
                    "due_week": 13,
                },
            ]
        elif "4-5" in context["assessment_count"]:
            assessments = [
                {
                    "id": 1,
                    "name": "Quiz 1",
                    "type": "Quiz",
                    "weight": "10%",
                    "due_week": 3,
                },
                {
                    "id": 2,
                    "name": "Assignment 1",
                    "type": "Individual Assignment",
                    "weight": "25%",
                    "due_week": 6,
                },
                {
                    "id": 3,
                    "name": "Group Project",
                    "type": "Group Work",
                    "weight": "25%",
                    "due_week": 9,
                },
                {
                    "id": 4,
                    "name": "Assignment 2",
                    "type": "Individual Assignment",
                    "weight": "20%",
                    "due_week": 11,
                },
                {
                    "id": 5,
                    "name": "Final Exam",
                    "type": "Examination",
                    "weight": "20%",
                    "due_week": 13,
                },
            ]
        else:  # 6+
            # Generate more frequent smaller assessments
            for i in range(1, 7):
                assessments.append(
                    {
                        "id": i,
                        "name": f"Assessment {i}",
                        "type": "Continuous Assessment",
                        "weight": f"{100 // 6}%",
                        "due_week": i * 2,
                    }
                )

        return assessments

    def _generate_teaching_activities(self, context: dict) -> dict:
        """Generate teaching activity suggestions (for AI-assisted)"""
        # This is a placeholder - real implementation would use LLM
        activities = {"lectures": [], "tutorials": [], "labs": [], "online": []}

        if "Lecture" in context["weekly_structure"]:
            activities["lectures"] = [
                "2-hour weekly lectures covering theoretical concepts"
            ]
        if "Tutorial" in context["weekly_structure"]:
            activities["tutorials"] = ["1-hour weekly tutorials for problem-solving"]
        if (
            "Lab" in context["weekly_structure"]
            or "Workshop" in context["weekly_structure"]
        ):
            activities["labs"] = ["2-hour weekly practical sessions"]
        if context["delivery_mode"] in ["Online", "Blended/Hybrid"]:
            activities["online"] = [
                "Asynchronous online materials and discussion forums"
            ]

        return activities

    async def _get_completion_next_steps(
        self, session: WorkflowChatSession
    ) -> list[str]:
        """Get next steps after workflow completion"""
        return [
            "Review generated unit structure",
            "Edit and refine content",
            "Generate detailed materials",
            "Export to your preferred format",
        ]

    async def _generate_stage_summary(self, session: WorkflowChatSession) -> str:
        """Generate a summary of decisions made in current stage"""
        stage = session.current_stage
        decisions = session.decisions_made or {}

        stage_questions = self.WORKFLOW_QUESTIONS.get(stage, [])
        summary_parts = []

        for question in stage_questions:
            if question.key in decisions:
                value = (
                    decisions[question.key].get("value")
                    if isinstance(decisions[question.key], dict)
                    else decisions[question.key]
                )
                summary_parts.append(f"{question.question}: {value}")

        return f"Stage '{stage}' completed. Decisions: " + "; ".join(summary_parts)
