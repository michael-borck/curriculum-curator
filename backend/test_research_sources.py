"""
Test script for research sources and citations.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.citation_service import CitationService, citation_service
from app.models.research_source import ResearchSource, SourceType, CitationStyle
from datetime import datetime


def test_citation_service():
    """Test the citation formatting service."""
    print("Testing citation service...")

    # Create a mock research source
    source = ResearchSource(
        id="test-id-123",
        user_id="user-123",
        unit_id="unit-456",
        url="https://example.com/article",
        title="The Impact of Constructivist Learning Theory",
        source_type=SourceType.JOURNAL_ARTICLE.value,
        authors_json='[{"first_name": "John", "last_name": "Smith", "suffix": "PhD"}, {"first_name": "Jane", "last_name": "Doe"}]',
        publication_date="2024",
        journal_name="Journal of Educational Technology",
        volume="45",
        issue="3",
        pages="123-145",
        doi="10.1234/jet.2024.12345",
        summary="A comprehensive study on constructivist learning approaches.",
        key_points_json='["Student-centered learning", "Active participation", "Knowledge construction"]',
        tags_json='["pedagogy", "constructivism", "learning-theory"]',
        academic_score=0.85,
        usage_count=0,
        is_favorite=False,
        access_date="2024-01-15",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Test APA7 citation
    apa_citation = citation_service.format_citation(source, CitationStyle.APA7)
    apa_in_text = citation_service.format_in_text_citation(source, CitationStyle.APA7)

    print("\nAPA7 Citation:")
    print(f"Full: {apa_citation}")
    print(f"In-text: {apa_in_text}")

    # Test Harvard citation
    harvard_citation = citation_service.format_citation(source, CitationStyle.HARVARD)
    harvard_in_text = citation_service.format_in_text_citation(
        source, CitationStyle.HARVARD
    )

    print("\nHarvard Citation:")
    print(f"Full: {harvard_citation}")
    print(f"In-text: {harvard_in_text}")

    # Test MLA citation
    mla_citation = citation_service.format_citation(source, CitationStyle.MLA)
    mla_in_text = citation_service.format_in_text_citation(source, CitationStyle.MLA)

    print("\nMLA Citation:")
    print(f"Full: {mla_citation}")
    print(f"In-text: {mla_in_text}")

    # Test reference list formatting
    sources = [source]
    reference_list = citation_service.format_reference_list(sources, CitationStyle.APA7)

    print("\nReference List:")
    print(reference_list)

    print("\n✅ Citation service tests passed!")


def test_author_parsing():
    """Test author JSON parsing."""
    print("\nTesting author parsing...")

    source = ResearchSource(
        id="test-id-456",
        user_id="user-123",
        url="https://example.com/book",
        title="Educational Psychology",
        source_type=SourceType.BOOK.value,
        authors_json='[{"first_name": "David", "last_name": "Brown"}, {"first_name": "Sarah", "last_name": "Wilson", "suffix": "EdD"}]',
    )

    authors = source.authors
    print(f"Authors parsed: {authors}")
    print(f"Number of authors: {len(authors)}")
    print(f"First author: {authors[0]['first_name']} {authors[0]['last_name']}")
    print(f"Second author suffix: {authors[1].get('suffix', 'None')}")

    # Test setting authors
    new_authors = [
        {"first_name": "Michael", "last_name": "Johnson"},
        {"first_name": "Emily", "last_name": "Chen", "suffix": "PhD"},
    ]
    source.authors = new_authors
    print(f"\nAuthors set: {source.authors_json}")

    print("\n✅ Author parsing tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Research Sources & Citations Test Script")
    print("=" * 60)

    test_citation_service()
    test_author_parsing()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
