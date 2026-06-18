"""
Unit tests for the multi-format grouping heuristic (Phase 3, Mode B).

Pure functions over file-path lists — no DB, no zip, no parsers. These
guard the canonical + source-files grouping rules from the
structured-import plan: same directory + same stem groups; canonical
ranking PPTX > DOCX > HTML > MD > PDF; unmatched files are singletons.
"""

from __future__ import annotations

from app.services.material_parsers.grouping import (
    CANONICAL_RANKING,
    group_files,
    select_canonical,
)


class TestSelectCanonical:
    def test_pptx_beats_everything(self) -> None:
        paths = [
            "lecture.pdf",
            "lecture.docx",
            "lecture.pptx",
            "lecture.html",
            "lecture.md",
        ]
        assert select_canonical(paths) == "lecture.pptx"

    def test_full_ranking_order(self) -> None:
        # Remove the winner one at a time; the next-ranked should surface.
        assert select_canonical(["a.docx", "a.html", "a.md", "a.pdf"]) == "a.docx"
        assert select_canonical(["a.html", "a.md", "a.pdf"]) == "a.html"
        assert select_canonical(["a.md", "a.pdf"]) == "a.md"
        assert select_canonical(["a.pdf"]) == "a.pdf"

    def test_htm_ranks_with_html(self) -> None:
        # htm sits between html and md in the ranking, below docx.
        assert select_canonical(["a.htm", "a.pdf"]) == "a.htm"
        assert select_canonical(["a.docx", "a.htm"]) == "a.docx"

    def test_unranked_only_loses_to_ranked(self) -> None:
        assert select_canonical(["a.pptx", "a.zip"]) == "a.pptx"

    def test_unranked_wins_when_nothing_ranked(self) -> None:
        # No ranked format present — first by input order wins.
        assert select_canonical(["a.xyz", "a.zip"]) == "a.xyz"

    def test_tie_broken_by_input_order(self) -> None:
        # Two PDFs (same rank): the first in input order wins.
        assert select_canonical(["second.pdf", "first.pdf"]) == "second.pdf"

    def test_ranking_constant_shape(self) -> None:
        assert CANONICAL_RANKING == ["pptx", "docx", "html", "htm", "md", "pdf"]


class TestGroupFiles:
    def test_same_dir_same_stem_groups(self) -> None:
        groups = group_files(["lecture_01.pptx", "lecture_01.pdf", "lecture_01.docx"])
        assert len(groups) == 1
        g = groups[0]
        assert g.name == "lecture_01"
        assert g.canonical == "lecture_01.pptx"
        assert set(g.source_files) == {"lecture_01.pdf", "lecture_01.docx"}
        assert not g.is_singleton

    def test_different_dirs_do_not_group(self) -> None:
        groups = group_files(["a/lecture.pptx", "b/lecture.pdf"])
        assert len(groups) == 2
        assert all(g.is_singleton for g in groups)

    def test_unmatched_files_are_singletons(self) -> None:
        groups = group_files(["lecture_01.pptx", "reading.pdf", "syllabus.docx"])
        assert len(groups) == 3
        assert all(g.is_singleton for g in groups)
        names = {g.name for g in groups}
        assert names == {"lecture_01", "reading", "syllabus"}

    def test_case_insensitive_stem_match(self) -> None:
        groups = group_files(["Lecture_01.pptx", "lecture_01.pdf"])
        assert len(groups) == 1
        # Name preserves the canonical file's original casing.
        assert groups[0].name == "Lecture_01"
        assert groups[0].canonical == "Lecture_01.pptx"

    def test_source_files_preserve_input_order(self) -> None:
        groups = group_files(["l.pptx", "l.pdf", "l.docx", "l.md"])
        g = groups[0]
        # Canonical excluded; the rest keep their input order.
        assert g.source_files == ["l.pdf", "l.docx", "l.md"]

    def test_groups_in_first_appearance_order(self) -> None:
        groups = group_files(["b.pptx", "a.pptx", "b.pdf", "a.pdf"])
        assert [g.name for g in groups] == ["b", "a"]

    def test_nested_directories_group_within_themselves(self) -> None:
        groups = group_files(
            [
                "week01/lecture.pptx",
                "week01/lecture.pdf",
                "week02/lecture.pptx",
            ]
        )
        assert len(groups) == 2
        week01 = next(g for g in groups if g.directory == "week01")
        assert week01.canonical == "week01/lecture.pptx"
        assert week01.source_files == ["week01/lecture.pdf"]
        week02 = next(g for g in groups if g.directory == "week02")
        assert week02.is_singleton

    def test_empty_input(self) -> None:
        assert group_files([]) == []

    def test_root_directory_is_empty_string(self) -> None:
        groups = group_files(["lecture.pptx"])
        assert groups[0].directory == ""
