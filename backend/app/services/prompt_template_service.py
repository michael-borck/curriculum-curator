"""
Service for managing prompt templates in the database
"""

import json
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate, TemplateStatus, TemplateType
from app.services.prompt_templates import PromptTemplate as PromptTemplateClass
from app.services.prompt_templates import PromptTemplateLibrary


class PromptTemplateService:
    """Service for managing prompt templates"""

    def __init__(self, db: Session):
        self.db = db

    def initialize_system_templates(self) -> None:
        """
        Initialize system templates from the library if they don't exist
        Called during app startup or migration
        """
        library = PromptTemplateLibrary()

        templates = [
            (TemplateType.UNIT_STRUCTURE, library.unit_structure_generation()),
            (TemplateType.LEARNING_OUTCOMES, library.learning_outcomes_refinement()),
            (TemplateType.LECTURE, library.lecture_content_generation()),
            (TemplateType.QUIZ, library.quiz_generation()),
            (TemplateType.RUBRIC, library.assessment_rubric_generation()),
            (TemplateType.CASE_STUDY, library.case_study_generation()),
        ]

        for template_type, template_obj in templates:
            # Check if system template exists
            existing = (
                self.db.query(PromptTemplate)
                .filter(
                    PromptTemplate.type == template_type,
                    PromptTemplate.is_system.is_(True),
                    PromptTemplate.status == TemplateStatus.ACTIVE,
                )
                .first()
            )

            if not existing:
                # Create system template
                db_template = PromptTemplate(
                    name=f"System: {template_type.value.replace('_', ' ').title()}",
                    description=template_obj.description,
                    type=template_type,
                    template_content=template_obj.template,
                    variables=json.dumps(template_obj.variables),
                    is_system=True,
                    is_public=True,
                    status=TemplateStatus.ACTIVE,
                )
                self.db.add(db_template)

        self.db.commit()

    def get_template(
        self,
        template_type: TemplateType,
        user_id: str | None = None,
        template_id: str | None = None,
    ) -> PromptTemplateClass | None:
        """
        Get a template by type, preferring user customizations

        Args:
            template_type: Type of template to retrieve
            user_id: User ID to check for custom templates
            template_id: Specific template ID to retrieve

        Returns:
            PromptTemplate instance or None
        """
        query = self.db.query(PromptTemplate).filter(
            PromptTemplate.status == TemplateStatus.ACTIVE
        )

        if template_id:
            # Get specific template
            db_template = query.filter(PromptTemplate.id == template_id).first()
        else:
            # Try user's custom template first
            if user_id:
                db_template = query.filter(
                    PromptTemplate.type == template_type,
                    PromptTemplate.owner_id == user_id,
                ).first()
            else:
                db_template = None

            # Fall back to system template
            if not db_template:
                db_template = query.filter(
                    PromptTemplate.type == template_type,
                    PromptTemplate.is_system.is_(True),
                ).first()

        if db_template:
            # Increment usage
            db_template.increment_usage()
            self.db.commit()

            # Convert to PromptTemplate class
            variables = (
                json.loads(db_template.variables) if db_template.variables else []
            )
            return PromptTemplateClass(
                template=db_template.template_content,
                description=db_template.description or "",
                variables=variables,
            )

        return None

    def create_custom_template(
        self,
        user_id: str,
        name: str,
        template_type: TemplateType,
        template_content: str,
        variables: list[str] | None = None,
        description: str | None = None,
        is_public: bool = False,
    ) -> PromptTemplate:
        """Create a custom template for a user"""
        db_template = PromptTemplate(
            name=name,
            description=description,
            type=template_type,
            template_content=template_content,
            variables=json.dumps(variables) if variables else None,
            owner_id=user_id,
            is_system=False,
            is_public=is_public,
            status=TemplateStatus.ACTIVE,
        )
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)

        return db_template

    def update_template(
        self,
        template_id: str,
        user_id: str,
        updates: dict[str, Any],
    ) -> PromptTemplate | None:
        """Update a user's custom template"""
        db_template = (
            self.db.query(PromptTemplate)
            .filter(
                PromptTemplate.id == template_id,
                PromptTemplate.owner_id == user_id,
                PromptTemplate.is_system.is_(False),
            )
            .first()
        )

        if not db_template:
            return None

        # Update allowed fields
        allowed_fields = [
            "name",
            "description",
            "template_content",
            "variables",
            "is_public",
            "status",
        ]
        for field, value in updates.items():
            if field in allowed_fields:
                field_value = value
                if field == "variables" and isinstance(value, list):
                    field_value = json.dumps(value)
                setattr(db_template, field, field_value)

        self.db.commit()
        self.db.refresh(db_template)

        return db_template

    def list_templates(
        self,
        user_id: str | None = None,
        template_type: TemplateType | None = None,
        include_public: bool = True,
        include_system: bool = True,
    ) -> list[PromptTemplate]:
        """List available templates for a user"""
        query = self.db.query(PromptTemplate).filter(
            PromptTemplate.status == TemplateStatus.ACTIVE
        )

        # Build OR conditions for visibility
        conditions = []

        if user_id:
            # User's own templates
            conditions.append(PromptTemplate.owner_id == user_id)

        if include_public:
            # Public templates
            conditions.append(PromptTemplate.is_public.is_(True))

        if include_system:
            # System templates
            conditions.append(PromptTemplate.is_system.is_(True))

        if conditions:
            query = query.filter(or_(*conditions))

        if template_type:
            query = query.filter(PromptTemplate.type == template_type)

        return query.order_by(
            PromptTemplate.is_system.desc(),
            PromptTemplate.usage_count.desc(),
        ).all()

    def duplicate_template(
        self,
        template_id: str,
        user_id: str,
        new_name: str | None = None,
    ) -> PromptTemplate | None:
        """Duplicate a template for customization"""
        source = (
            self.db.query(PromptTemplate)
            .filter(PromptTemplate.id == template_id)
            .first()
        )

        if not source:
            return None

        # Check if user can access this template
        can_access = source.is_system or source.is_public or source.owner_id == user_id

        if not can_access:
            return None

        # Create duplicate
        duplicate = PromptTemplate(
            name=new_name or f"{source.name} (Copy)",
            description=source.description,
            type=source.type,
            template_content=source.template_content,
            variables=source.variables,
            owner_id=user_id,
            is_system=False,
            is_public=False,
            parent_id=source.id,
            tags=source.tags,
            model_preferences=source.model_preferences,
        )

        self.db.add(duplicate)
        self.db.commit()
        self.db.refresh(duplicate)

        return duplicate

    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a user's custom template"""
        db_template = (
            self.db.query(PromptTemplate)
            .filter(
                PromptTemplate.id == template_id,
                PromptTemplate.owner_id == user_id,
                PromptTemplate.is_system.is_(False),
            )
            .first()
        )

        if not db_template:
            return False

        # Soft delete by setting status
        db_template.status = TemplateStatus.ARCHIVED
        self.db.commit()

        return True
