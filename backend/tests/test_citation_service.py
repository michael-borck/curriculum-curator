"""
Tests for Citation service — pure string formatting logic, no DB needed.
"""

import json

import pytest

from app.models.research_source import CitationStyle, ResearchSource, SourceType
from app.services.citation_service import Author, CitationService


@pytest.fixture
def svc() -> CitationService:
    return CitationService()


def _make_source(
    title: str = "Machine Learning in Education",
    source_type: str = SourceType.JOURNAL_ARTICLE.value,
    authors: list[dict[str, str]] | None = None,
    publication_date: str = "2024",
    journal_name: str | None = "Journal of AI",
    volume: str | None = "12",
    issue: str | None = "3",
    pages: str | None = "45-67",
    doi: str | None = "10.1234/jai.2024.001",
    publisher: str | None = None,
    url: str = "https://example.com/article",
    access_date: str | None = "March 15, 2024",
) -> ResearchSource:
    if authors is None:
        authors = [{"first_name": "John", "last_name": "Smith"}]
    src = ResearchSource(
        title=title,
        source_type=source_type,
        publication_date=publication_date,
        journal_name=journal_name,
        volume=volume,
        issue=issue,
        pages=pages,
        doi=doi,
        publisher=publisher,
        url=url,
        access_date=access_date,
        user_id="fake-user-id",
    )
    src.authors_json = json.dumps(authors)
    return src


# ─── AUTHOR PARSING ──────────────────────────────────────────


class TestAuthorParsing:
    def test_author_from_dict(self):
        a = Author.from_dict(
            {"first_name": "Jane", "last_name": "Doe", "suffix": "Jr."}
        )
        assert a.first_name == "Jane"
        assert a.last_name == "Doe"
        assert a.suffix == "Jr."

    def test_author_from_dict_missing_fields(self):
        a = Author.from_dict({})
        assert a.first_name == ""
        assert a.last_name == ""
        assert a.suffix is None


# ─── APA7 ────────────────────────────────────────────────────


class TestAPA7:
    def test_journal_article(self, svc: CitationService):
        source = _make_source()
        result = svc.format_citation(source, CitationStyle.APA7)
        assert "Smith, J." in result
        assert "(2024)" in result
        assert "Machine Learning in Education" in result
        assert "*Journal of AI*" in result
        assert "https://doi.org/10.1234" in result

    def test_book(self, svc: CitationService):
        source = _make_source(
            source_type=SourceType.BOOK.value,
            publisher="Academic Press",
            journal_name=None,
        )
        result = svc.format_citation(source, CitationStyle.APA7)
        assert "Academic Press" in result
        assert "*Machine Learning in Education*" in result

    def test_website(self, svc: CitationService):
        source = _make_source(source_type=SourceType.WEBSITE.value)
        result = svc.format_citation(source, CitationStyle.APA7)
        assert "Retrieved" in result
        assert "https://example.com/article" in result

    def test_in_text_single_author(self, svc: CitationService):
        source = _make_source()
        result = svc.format_in_text_citation(source, CitationStyle.APA7)
        assert result == "(Smith, 2024)"

    def test_in_text_two_authors(self, svc: CitationService):
        source = _make_source(
            authors=[
                {"first_name": "John", "last_name": "Smith"},
                {"first_name": "Jane", "last_name": "Doe"},
            ]
        )
        result = svc.format_in_text_citation(source, CitationStyle.APA7)
        assert result == "(Smith & Doe, 2024)"

    def test_in_text_three_plus_authors(self, svc: CitationService):
        source = _make_source(
            authors=[
                {"first_name": "A", "last_name": "Alpha"},
                {"first_name": "B", "last_name": "Beta"},
                {"first_name": "C", "last_name": "Gamma"},
            ]
        )
        result = svc.format_in_text_citation(source, CitationStyle.APA7)
        assert "et al." in result
        assert "Alpha" in result

    def test_in_text_no_authors(self, svc: CitationService):
        source = _make_source(authors=[])
        result = svc.format_in_text_citation(source, CitationStyle.APA7)
        assert "2024" in result

    def test_no_date(self, svc: CitationService):
        source = _make_source(publication_date=None)
        result = svc.format_citation(source, CitationStyle.APA7)
        assert "n.d." in result


# ─── HARVARD ─────────────────────────────────────────────────


class TestHarvard:
    def test_journal_article(self, svc: CitationService):
        source = _make_source()
        result = svc.format_citation(source, CitationStyle.HARVARD)
        assert "vol." in result
        assert "no." in result

    def test_in_text(self, svc: CitationService):
        source = _make_source()
        result = svc.format_in_text_citation(source, CitationStyle.HARVARD)
        # Harvard uses "Author Year" without comma
        assert "Smith" in result
        assert "2024" in result


# ─── MLA ─────────────────────────────────────────────────────


class TestMLA:
    def test_journal_article(self, svc: CitationService):
        source = _make_source()
        result = svc.format_citation(source, CitationStyle.MLA)
        assert '"Machine Learning in Education."' in result

    def test_in_text(self, svc: CitationService):
        source = _make_source()
        result = svc.format_in_text_citation(source, CitationStyle.MLA)
        assert result == "(Smith)"

    def test_in_text_two_authors(self, svc: CitationService):
        source = _make_source(
            authors=[
                {"first_name": "John", "last_name": "Smith"},
                {"first_name": "Jane", "last_name": "Doe"},
            ]
        )
        result = svc.format_in_text_citation(source, CitationStyle.MLA)
        assert "Smith and Doe" in result


# ─── CHICAGO ─────────────────────────────────────────────────


class TestChicago:
    def test_journal_article(self, svc: CitationService):
        source = _make_source()
        result = svc.format_citation(source, CitationStyle.CHICAGO)
        assert "(2024)" in result

    def test_in_text_delegates_to_apa(self, svc: CitationService):
        source = _make_source()
        result = svc.format_in_text_citation(source, CitationStyle.CHICAGO)
        assert result == "(Smith, 2024)"


# ─── IEEE ────────────────────────────────────────────────────


class TestIEEE:
    def test_journal_article(self, svc: CitationService):
        source = _make_source()
        result = svc.format_citation(source, CitationStyle.IEEE)
        assert "vol." in result
        assert "2024." in result

    def test_website(self, svc: CitationService):
        source = _make_source(source_type=SourceType.WEBSITE.value)
        result = svc.format_citation(source, CitationStyle.IEEE)
        assert "[Online]" in result
        assert "Accessed" in result

    def test_in_text_is_placeholder(self, svc: CitationService):
        source = _make_source()
        assert svc.format_in_text_citation(source, CitationStyle.IEEE) == "[N]"


# ─── VANCOUVER ───────────────────────────────────────────────


class TestVancouver:
    def test_journal_article(self, svc: CitationService):
        source = _make_source()
        result = svc.format_citation(source, CitationStyle.VANCOUVER)
        # Vancouver: Authors. Title. Journal. Year;Volume(Issue):Pages.
        assert "Smith J" in result  # no period in initials
        assert "2024" in result

    def test_in_text_is_placeholder(self, svc: CitationService):
        source = _make_source()
        assert svc.format_in_text_citation(source, CitationStyle.VANCOUVER) == "(N)"


# ─── REFERENCE LIST ──────────────────────────────────────────


class TestReferenceList:
    def test_empty_list(self, svc: CitationService):
        assert svc.format_reference_list([]) == ""

    def test_alphabetical_list(self, svc: CitationService):
        s1 = _make_source(
            title="Alpha", authors=[{"first_name": "B", "last_name": "Beta"}]
        )
        s2 = _make_source(
            title="Zeta", authors=[{"first_name": "A", "last_name": "Alpha"}]
        )
        result = svc.format_reference_list([s1, s2], CitationStyle.APA7)
        # Alpha should come before Beta alphabetically
        idx_alpha = result.index("Alpha, A.")
        idx_beta = result.index("Beta, B.")
        assert idx_alpha < idx_beta

    def test_ieee_numbered_list(self, svc: CitationService):
        s1 = _make_source(title="First")
        s2 = _make_source(title="Second")
        result = svc.format_reference_list([s1, s2], CitationStyle.IEEE)
        assert "[1]" in result
        assert "[2]" in result

    def test_vancouver_numbered_list(self, svc: CitationService):
        s1 = _make_source(title="First")
        s2 = _make_source(title="Second")
        result = svc.format_reference_list([s1, s2], CitationStyle.VANCOUVER)
        assert "1." in result
        assert "2." in result


# ─── HELPER METHODS ──────────────────────────────────────────


class TestHelpers:
    def test_get_year_iso(self, svc: CitationService):
        source = _make_source(publication_date="2024-03-15")
        assert svc._get_year(source) == "2024"

    def test_get_year_partial(self, svc: CitationService):
        source = _make_source(publication_date="2024")
        assert svc._get_year(source) == "2024"

    def test_get_year_none(self, svc: CitationService):
        source = _make_source(publication_date=None)
        assert svc._get_year(source) == "n.d."

    def test_get_initials(self, svc: CitationService):
        assert svc._get_initials("John Michael") == "J. M."
        assert svc._get_initials("John Michael", with_periods=False) == "JM"
        assert svc._get_initials("") == ""

    def test_format_authors_apa_many(self, svc: CitationService):
        authors = [
            Author(first_name=f"Author{i}", last_name=f"Last{i}") for i in range(21)
        ]
        result = svc._format_authors_apa(authors)
        assert "..." in result

    def test_format_authors_mla_four_plus(self, svc: CitationService):
        authors = [Author(first_name=f"A{i}", last_name=f"L{i}") for i in range(4)]
        result = svc._format_authors_mla(authors)
        assert "et al." in result

    def test_format_authors_vancouver_seven_plus(self, svc: CitationService):
        authors = [Author(first_name=f"A{i}", last_name=f"L{i}") for i in range(8)]
        result = svc._format_authors_vancouver(authors)
        assert "et al." in result
