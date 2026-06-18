"""Tests for export capability detection and warnings (story 9.21)."""

from app.services.export.capabilities import (
    FORMAT_CAPABILITIES,
    ContentFeatures,
    detect_content_features,
    warnings_for,
)


def _quiz_node(question_type: str) -> dict:
    return {
        "type": "quizQuestion",
        "attrs": {
            "questionId": "q1",
            "questionText": "Pick one",
            "questionType": question_type,
            "options": [
                {"text": "a", "correct": True},
                {"text": "b", "correct": False},
            ],
        },
    }


def _doc(*content: dict) -> dict:
    return {"type": "doc", "content": list(content)}


class TestDetectFeatures:
    def test_collects_question_types(self):
        doc = _doc(_quiz_node("matching"), _quiz_node("multiple_choice"))
        features = detect_content_features(doc)
        assert features.question_types == {"matching", "multiple_choice"}

    def test_detects_structural_nodes(self):
        doc = _doc(
            {"type": "table", "content": []},
            {"type": "image", "attrs": {"src": "x.png"}},
            {"type": "mermaid", "attrs": {"code": "graph TD"}},
        )
        features = detect_content_features(doc)
        assert features.has_tables
        assert features.has_images
        assert features.has_mermaid

    def test_empty_content(self):
        features = detect_content_features(None)
        assert features.question_types == set()
        assert not features.has_video


class TestWarnings:
    def test_h5p_converts_matching_to_multiple_choice(self):
        features = ContentFeatures(question_types={"matching"})
        warnings = warnings_for("quiz", "h5p_question_set", features)
        assert len(warnings) == 1
        assert warnings[0].severity == "converted"
        assert "multiple choice" in warnings[0].message.lower()
        # QTI does support matching, so it's the suggested alternative
        assert warnings[0].suggested_target == "qti"

    def test_qti_supports_all_current_types_no_warning(self):
        features = ContentFeatures(
            question_types={
                "multiple_choice",
                "true_false",
                "short_answer",
                "fill_in_blank",
                "matching",
                "long_answer",
            }
        )
        assert warnings_for("quiz", "qti", features) == []

    def test_h5p_supports_basic_types_no_warning(self):
        features = ContentFeatures(
            question_types={"multiple_choice", "true_false", "fill_in_blank"}
        )
        assert warnings_for("quiz", "h5p_question_set", features) == []

    def test_drag_drop_dropped_by_qti_suggests_h5p(self):
        features = ContentFeatures(question_types={"drag_drop"})
        warnings = warnings_for("quiz", "qti", features)
        assert len(warnings) == 1
        assert warnings[0].severity == "dropped"
        # H5P DragText supports it, so it's the suggested alternative
        assert warnings[0].suggested_target == "h5p_question_set"

    def test_drag_drop_supported_by_h5p_no_warning(self):
        features = ContentFeatures(question_types={"drag_drop"})
        assert warnings_for("quiz", "h5p_question_set", features) == []

    def test_interactive_video_drops_video_on_quiz_target(self):
        features = ContentFeatures(has_video=True)
        warnings = warnings_for("interactive_video", "qti", features)
        assert len(warnings) == 1
        assert warnings[0].severity == "dropped"
        assert warnings[0].suggested_target == "h5p_interactive_video"

    def test_interactive_video_no_warning_on_video_target(self):
        features = ContentFeatures(has_video=True)
        assert (
            warnings_for("interactive_video", "h5p_interactive_video", features) == []
        )

    def test_unknown_target_no_warning(self):
        features = ContentFeatures(question_types={"matching"})
        assert warnings_for("quiz", "pdf", features) == []


class TestMatrixDriftGuard:
    """Pin the capability matrix to the real adapters so it can't drift."""

    def test_qti_matrix_matches_adapter(self):
        from app.services.unit_export_data import InMemoryQuizQuestion

        def make(qtype: str) -> InMemoryQuizQuestion:
            return InMemoryQuizQuestion(
                question_id="q",
                question_text="text",
                question_type=qtype,
                options=[{"text": "a"}, {"text": "b"}],
                correct_answers=["a"],
                answer_explanation=None,
                points=1.0,
                order_index=0,
            )

        from app.services.qti_service import qti_exporter

        # Every type the matrix claims QTI supports must produce a real item
        for qtype in FORMAT_CAPABILITIES["qti"].question_types:
            item = qti_exporter._question_to_qti21(make(qtype), "i1")
            assert item is not None, f"QTI matrix claims {qtype} but adapter drops it"

        # A type outside the matrix is genuinely dropped (returns None)
        assert qti_exporter._question_to_qti21(make("drag_drop"), "i1") is None

    def test_h5p_matrix_matches_adapter(self):
        from app.services.h5p_service import _TYPE_MAP

        # Each type the matrix claims H5P models faithfully has its own library
        for qtype in FORMAT_CAPABILITIES["h5p_question_set"].question_types:
            assert qtype in _TYPE_MAP, (
                f"H5P matrix claims {qtype} but adapter has no dedicated library"
            )

        # 'matching' is deliberately NOT modelled — it hits the MultiChoice
        # fallback, which is exactly the 'converted' warning the matrix emits.
        assert "matching" not in _TYPE_MAP


class TestPreviewEndpointWarnings:
    """The warnings surface through the material export-preview endpoint."""

    def test_matching_quiz_warns_for_h5p(self, client, test_db, test_unit):
        from app.models.weekly_material import WeeklyMaterial

        material = WeeklyMaterial(
            unit_id=test_unit.id,
            week_number=1,
            title="Matching quiz",
            type="lecture",
            content_json=_doc(_quiz_node("matching")),
        )
        test_db.add(material)
        test_db.commit()
        test_db.refresh(material)

        resp = client.get(f"/api/materials/{material.id}/export/preview")
        assert resp.status_code == 200
        warnings = resp.json()["warnings"]
        # h5p_question_set converts matching; qti does not warn
        assert "quiz:h5p_question_set" in warnings
        assert warnings["quiz:h5p_question_set"][0]["severity"] == "converted"
        assert "quiz:qti" not in warnings

    def test_plain_material_has_no_warnings(self, client, test_db, test_unit):
        from app.models.weekly_material import WeeklyMaterial

        material = WeeklyMaterial(
            unit_id=test_unit.id,
            week_number=1,
            title="Plain",
            type="lecture",
            content_json=_doc(
                {"type": "paragraph", "content": [{"type": "text", "text": "hi"}]}
            ),
        )
        test_db.add(material)
        test_db.commit()
        test_db.refresh(material)

        resp = client.get(f"/api/materials/{material.id}/export/preview")
        assert resp.status_code == 200
        assert resp.json()["warnings"] == {}
