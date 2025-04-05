"""Tests for specific remediators."""

from types import SimpleNamespace

import pytest

from curriculum_curator.remediation.remediators.autofix.format_corrector import (
    FormatCorrector,
)
from curriculum_curator.remediation.remediators.autofix.sentence_splitter import (
    SentenceSplitter,
)
from curriculum_curator.validation.manager import ValidationIssue


@pytest.fixture
def format_corrector():
    """Create a format corrector with test configuration."""
    config = SimpleNamespace(aggressive=False)
    return FormatCorrector(config)


@pytest.fixture
def sentence_splitter():
    """Create a sentence splitter with test configuration."""
    config = SimpleNamespace(max_sentence_length=20)
    return SentenceSplitter(config)


class TestFormatCorrector:
    """Tests for the format corrector remediator."""

    @pytest.mark.asyncio
    async def test_remediate(self, format_corrector):
        """Test format correction remediation."""
        content = """
        # Title with inconsistent Formatting

        This paragraph has some inconsistent    spacing   and   formatting.

        - item 1
        * item 2 (inconsistent list marker)
        - item 3

        ```
        code block with   extra  spaces
        ```
        """

        issues = [
            ValidationIssue(
                severity="warning", message="Inconsistent formatting", location="document"
            )
        ]

        result = await format_corrector.remediate(content, issues)

        # Check that the result contains expected fields
        assert "content" in result
        assert "actions" in result

        remediated_content = result["content"]
        actions = result["actions"]

        # Content should be different after remediation
        assert remediated_content != content

        # Some specific fixes we expect
        assert "    spacing   and   formatting" not in remediated_content

        # There should be at least one action recorded
        assert len(actions) > 0

    @pytest.mark.asyncio
    async def test_should_remediate(self, format_corrector):
        """Test should_remediate decision logic."""
        issues = [
            ValidationIssue(
                severity="warning",
                message="Inconsistent formatting",
                location="document",
                remediation_type="auto_fix.format_corrector",
            )
        ]

        assert format_corrector.should_remediate(issues)

        # No issues means no remediation needed
        assert not format_corrector.should_remediate([])

        # Issues with different remediation types should not be handled
        other_issues = [
            ValidationIssue(
                severity="warning",
                message="Long sentences",
                location="document",
                remediation_type="auto_fix.sentence_splitter",
            )
        ]
        assert not format_corrector.should_remediate(other_issues)


class TestSentenceSplitter:
    """Tests for the sentence splitter remediator."""

    @pytest.mark.asyncio
    async def test_remediate(self, sentence_splitter):
        """Test sentence splitting remediation."""
        content = """
        This is a very long sentence that exceeds the maximum allowed sentence length and should be split into smaller sentences by the sentence splitter remediator because it's hard to read.

        This sentence is fine because it's short.

        Here's another very long sentence that goes on and on with unnecessary words and clauses that make it difficult to follow the main point and loses the reader's attention.
        """

        issues = [
            ValidationIssue(
                severity="warning",
                message="Sentences are too long",
                location="document",
                remediation_type="auto_fix.sentence_splitter",
            )
        ]

        result = await sentence_splitter.remediate(content, issues)

        # Check that the result contains expected fields
        assert "content" in result
        assert "actions" in result

        remediated_content = result["content"]
        actions = result["actions"]

        # Content should be different after remediation
        assert remediated_content != content

        # Long sentences should be split, resulting in more sentences
        content_sentence_count = content.count(".")
        remediated_sentence_count = remediated_content.count(".")
        assert remediated_sentence_count > content_sentence_count

        # There should be at least one action recorded
        assert len(actions) > 0

    @pytest.mark.asyncio
    async def test_split_sentences(self, sentence_splitter):
        """Test the sentence splitting logic directly."""
        long_sentence = "This is a very long sentence that exceeds the maximum allowed sentence length and should be split into smaller sentences by the sentence splitter remediator because it's hard to read."

        split_result = await sentence_splitter.split_sentences(long_sentence)

        # The result should be a list of shorter sentences
        assert isinstance(split_result, list)
        assert len(split_result) > 1

        # Each sentence should be shorter than the original
        for sentence in split_result:
            assert len(sentence) < len(long_sentence)

        # Each sentence should end with proper punctuation
        for sentence in split_result:
            assert sentence.strip()[-1] in [".", "?", "!"]
