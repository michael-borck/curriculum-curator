"""
Tests for Prompt Template service using in-memory SQLite.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate, TemplateStatus, TemplateType
from app.models.user import User
from app.services.prompt_template_service import PromptTemplateService


def _make_system_template(
    db: Session,
    template_type: TemplateType = TemplateType.LECTURE,
    name: str = "System Lecture",
) -> PromptTemplate:
    t = PromptTemplate(
        name=name,
        description="A system template",
        type=template_type.value,
        template_content="Generate a lecture about {topic}",
        variables='["topic"]',
        is_system=True,
        is_public=True,
        status=TemplateStatus.ACTIVE.value,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ─── CREATE CUSTOM TEMPLATE ─────────────────────────────────


class TestCreateCustomTemplate:
    def test_create(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        result = svc.create_custom_template(
            user_id=test_user.id,
            name="My Custom Template",
            template_type=TemplateType.QUIZ,
            template_content="Generate a quiz about {topic}",
            variables=["topic"],
            description="Custom quiz generator",
        )
        assert result.name == "My Custom Template"
        assert result.type == TemplateType.QUIZ.value
        assert result.is_system is False
        assert result.owner_id == test_user.id

    def test_create_public(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        result = svc.create_custom_template(
            user_id=test_user.id,
            name="Public Template",
            template_type=TemplateType.LECTURE,
            template_content="Content here",
            is_public=True,
        )
        assert result.is_public is True


# ─── GET TEMPLATE ────────────────────────────────────────────


class TestGetTemplate:
    def test_get_system_template(self, test_db: Session):
        _make_system_template(test_db, TemplateType.LECTURE)
        svc = PromptTemplateService(test_db)

        result = svc.get_template(TemplateType.LECTURE)
        assert result is not None
        assert "lecture" in result.template.lower() or "Generate" in result.template

    def test_user_custom_overrides_system(self, test_db: Session, test_user: User):
        _make_system_template(test_db, TemplateType.QUIZ)
        svc = PromptTemplateService(test_db)

        # Create user custom
        svc.create_custom_template(
            user_id=test_user.id,
            name="User Quiz",
            template_type=TemplateType.QUIZ,
            template_content="My custom quiz: {topic}",
            variables=["topic"],
        )

        result = svc.get_template(TemplateType.QUIZ, user_id=test_user.id)
        assert result is not None
        assert "custom quiz" in result.template.lower()

    def test_get_by_id(self, test_db: Session):
        template = _make_system_template(test_db)
        svc = PromptTemplateService(test_db)

        result = svc.get_template(TemplateType.LECTURE, template_id=template.id)
        assert result is not None

    def test_get_nonexistent_returns_none(self, test_db: Session):
        svc = PromptTemplateService(test_db)
        result = svc.get_template(TemplateType.RUBRIC)
        assert result is None

    def test_get_increments_usage(self, test_db: Session):
        template = _make_system_template(test_db)
        assert template.usage_count == 0

        svc = PromptTemplateService(test_db)
        svc.get_template(TemplateType.LECTURE)

        test_db.refresh(template)
        assert template.usage_count == 1


# ─── UPDATE TEMPLATE ─────────────────────────────────────────


class TestUpdateTemplate:
    def test_update_own_template(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        custom = svc.create_custom_template(
            user_id=test_user.id,
            name="Original",
            template_type=TemplateType.LECTURE,
            template_content="Original content",
        )

        result = svc.update_template(
            template_id=custom.id,
            user_id=test_user.id,
            updates={"name": "Updated Name", "template_content": "New content"},
        )
        assert result is not None
        assert result.name == "Updated Name"
        assert result.template_content == "New content"

    def test_cannot_update_system_template(self, test_db: Session, test_user: User):
        sys_template = _make_system_template(test_db)
        svc = PromptTemplateService(test_db)

        result = svc.update_template(
            template_id=sys_template.id,
            user_id=test_user.id,
            updates={"name": "Hacked"},
        )
        assert result is None

    def test_cannot_update_other_users_template(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        custom = svc.create_custom_template(
            user_id=test_user.id,
            name="Mine",
            template_type=TemplateType.LECTURE,
            template_content="Content",
        )

        other_user_id = str(uuid.uuid4())
        result = svc.update_template(
            template_id=custom.id,
            user_id=other_user_id,
            updates={"name": "Stolen"},
        )
        assert result is None

    def test_update_variables_serialized(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        custom = svc.create_custom_template(
            user_id=test_user.id,
            name="With Vars",
            template_type=TemplateType.LECTURE,
            template_content="Content {a} {b}",
        )

        result = svc.update_template(
            template_id=custom.id,
            user_id=test_user.id,
            updates={"variables": ["a", "b"]},
        )
        assert result is not None
        assert '"a"' in result.variables


# ─── LIST TEMPLATES ──────────────────────────────────────────


class TestListTemplates:
    def test_list_system_templates(self, test_db: Session):
        _make_system_template(test_db, TemplateType.LECTURE, name="Sys1")
        _make_system_template(test_db, TemplateType.QUIZ, name="Sys2")
        svc = PromptTemplateService(test_db)

        results = svc.list_templates()
        assert len(results) >= 2

    def test_list_by_type(self, test_db: Session):
        _make_system_template(test_db, TemplateType.LECTURE)
        _make_system_template(test_db, TemplateType.QUIZ)
        svc = PromptTemplateService(test_db)

        results = svc.list_templates(template_type=TemplateType.QUIZ)
        assert all(t.type == TemplateType.QUIZ.value for t in results)

    def test_list_includes_user_and_public(self, test_db: Session, test_user: User):
        _make_system_template(test_db)
        svc = PromptTemplateService(test_db)
        svc.create_custom_template(
            user_id=test_user.id,
            name="Private",
            template_type=TemplateType.LECTURE,
            template_content="Private",
            is_public=False,
        )

        results = svc.list_templates(user_id=test_user.id)
        assert len(results) >= 2  # System + user's private


# ─── DUPLICATE TEMPLATE ──────────────────────────────────────


class TestDuplicateTemplate:
    def test_duplicate_system_template(self, test_db: Session, test_user: User):
        sys_template = _make_system_template(test_db)
        svc = PromptTemplateService(test_db)

        result = svc.duplicate_template(sys_template.id, test_user.id, "My Copy")
        assert result is not None
        assert result.name == "My Copy"
        assert result.owner_id == test_user.id
        assert result.is_system is False
        assert result.parent_id == sys_template.id

    def test_duplicate_default_name(self, test_db: Session, test_user: User):
        sys_template = _make_system_template(test_db, name="Original")
        svc = PromptTemplateService(test_db)

        result = svc.duplicate_template(sys_template.id, test_user.id)
        assert result is not None
        assert "(Copy)" in result.name

    def test_duplicate_nonexistent_returns_none(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        result = svc.duplicate_template(str(uuid.uuid4()), test_user.id)
        assert result is None

    def test_cannot_duplicate_private_from_other_user(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        private = svc.create_custom_template(
            user_id=test_user.id,
            name="Private",
            template_type=TemplateType.LECTURE,
            template_content="Content",
            is_public=False,
        )

        other_user_id = str(uuid.uuid4())
        result = svc.duplicate_template(private.id, other_user_id)
        assert result is None


# ─── DELETE TEMPLATE ─────────────────────────────────────────


class TestDeleteTemplate:
    def test_delete_own_template(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        custom = svc.create_custom_template(
            user_id=test_user.id,
            name="To Delete",
            template_type=TemplateType.LECTURE,
            template_content="Content",
        )

        result = svc.delete_template(custom.id, test_user.id)
        assert result is True

        # Verify it's archived (soft delete)
        test_db.refresh(custom)
        assert custom.status == TemplateStatus.ARCHIVED.value

    def test_cannot_delete_system_template(self, test_db: Session, test_user: User):
        sys_template = _make_system_template(test_db)
        svc = PromptTemplateService(test_db)

        result = svc.delete_template(sys_template.id, test_user.id)
        assert result is False

    def test_delete_nonexistent_returns_false(self, test_db: Session, test_user: User):
        svc = PromptTemplateService(test_db)
        result = svc.delete_template(str(uuid.uuid4()), test_user.id)
        assert result is False
