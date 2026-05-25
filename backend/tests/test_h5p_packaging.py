"""Tests for the shared H5P packaging helper (candidate #6)."""

import json
import zipfile

from app.services.h5p_packaging import build_manifest, pack_h5p


def test_build_manifest_shape() -> None:
    deps = [{"machineName": "H5P.QuestionSet", "majorVersion": 1, "minorVersion": 20}]
    manifest = build_manifest("My Quiz", "H5P.QuestionSet", deps)
    assert manifest == {
        "title": "My Quiz",
        "mainLibrary": "H5P.QuestionSet",
        "language": "en",
        "embedTypes": ["div", "iframe"],
        "preloadedDependencies": deps,
    }


def test_pack_h5p_produces_valid_zip() -> None:
    content = {"questions": [], "progressType": "dots"}
    manifest = build_manifest("T", "H5P.CoursePresentation", [])
    buf = pack_h5p(content, manifest)

    with zipfile.ZipFile(buf) as zf:
        assert set(zf.namelist()) == {"h5p.json", "content/content.json"}
        assert json.loads(zf.read("h5p.json")) == manifest
        assert json.loads(zf.read("content/content.json")) == content
