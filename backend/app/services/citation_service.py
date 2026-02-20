"""
Citation formatting service for academic references.

Supports multiple citation styles: APA7, Harvard, MLA, Chicago, IEEE, Vancouver.
"""

import re
from dataclasses import dataclass
from datetime import datetime

from app.models.research_source import CitationStyle, ResearchSource, SourceType


@dataclass
class Author:
    """Represents an author for citation formatting."""

    first_name: str
    last_name: str
    suffix: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Author":
        """Create Author from dictionary."""
        return cls(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            suffix=data.get("suffix"),
        )


class CitationService:
    """Service for formatting academic citations in various styles."""

    def format_citation(
        self,
        source: ResearchSource,
        style: CitationStyle = CitationStyle.APA7,
    ) -> str:
        """
        Format a full reference citation for a source.

        Args:
            source: The research source to format
            style: The citation style to use

        Returns:
            Formatted citation string
        """
        formatters = {
            CitationStyle.APA7: self._format_apa7,
            CitationStyle.HARVARD: self._format_harvard,
            CitationStyle.MLA: self._format_mla,
            CitationStyle.CHICAGO: self._format_chicago,
            CitationStyle.IEEE: self._format_ieee,
            CitationStyle.VANCOUVER: self._format_vancouver,
        }

        formatter = formatters.get(style, self._format_apa7)
        return formatter(source)

    def format_in_text_citation(
        self,
        source: ResearchSource,
        style: CitationStyle = CitationStyle.APA7,
    ) -> str:
        """
        Format an in-text citation for a source.

        Args:
            source: The research source to format
            style: The citation style to use

        Returns:
            Formatted in-text citation (e.g., "(Smith, 2024)")
        """
        formatters = {
            CitationStyle.APA7: self._in_text_apa7,
            CitationStyle.HARVARD: self._in_text_harvard,
            CitationStyle.MLA: self._in_text_mla,
            CitationStyle.CHICAGO: self._in_text_chicago,
            CitationStyle.IEEE: self._in_text_ieee,
            CitationStyle.VANCOUVER: self._in_text_vancouver,
        }

        formatter = formatters.get(style, self._in_text_apa7)
        return formatter(source)

    def format_reference_list(
        self,
        sources: list[ResearchSource],
        style: CitationStyle = CitationStyle.APA7,
    ) -> str:
        """
        Format a complete reference list from multiple sources.

        Args:
            sources: List of research sources
            style: The citation style to use

        Returns:
            Formatted reference list with proper sorting and numbering
        """
        if not sources:
            return ""

        # Sort sources appropriately for the style
        if style in {CitationStyle.IEEE, CitationStyle.VANCOUVER}:
            # Numbered styles - keep order as provided (order of appearance)
            sorted_sources = sources
        else:
            # Alphabetical styles - sort by first author's last name
            sorted_sources = sorted(
                sources,
                key=lambda s: self._get_first_author_last_name(s).lower(),
            )

        # Format each citation
        citations = []
        for i, source in enumerate(sorted_sources, 1):
            citation = self.format_citation(source, style)
            if style == CitationStyle.IEEE:
                citations.append(f"[{i}] {citation}")
            elif style == CitationStyle.VANCOUVER:
                citations.append(f"{i}. {citation}")
            else:
                citations.append(citation)

        return "\n\n".join(citations)

    # ==================== Helper Methods ====================

    def _get_authors(self, source: ResearchSource) -> list[Author]:
        """Parse authors from source."""
        return [Author.from_dict(a) for a in source.authors]

    def _get_first_author_last_name(self, source: ResearchSource) -> str:
        """Get the last name of the first author."""
        authors = self._get_authors(source)
        if authors:
            return authors[0].last_name
        return "Unknown"

    def _get_year(self, source: ResearchSource) -> str:
        """Extract year from publication date."""
        if not source.publication_date:
            return "n.d."
        # Handle formats: "2024", "2024-03", "2024-03-15"
        match = re.match(r"(\d{4})", source.publication_date)
        return match.group(1) if match else "n.d."

    def _format_authors_apa(self, authors: list[Author], max_authors: int = 20) -> str:
        """Format authors in APA style: Last, F. M., & Last, F. M."""
        if not authors:
            return ""

        if len(authors) == 1:
            a = authors[0]
            initials = self._get_initials(a.first_name)
            return f"{a.last_name}, {initials}"

        if len(authors) == 2:
            formatted = []
            for a in authors:
                initials = self._get_initials(a.first_name)
                formatted.append(f"{a.last_name}, {initials}")
            return f"{formatted[0]}, & {formatted[1]}"

        if len(authors) <= max_authors:
            formatted = []
            for i, a in enumerate(authors):
                initials = self._get_initials(a.first_name)
                if i == len(authors) - 1:
                    formatted.append(f"& {a.last_name}, {initials}")
                else:
                    formatted.append(f"{a.last_name}, {initials}")
            return ", ".join(formatted)

        # More than max_authors: First 19, ..., & Last
        formatted = []
        for a in authors[:19]:
            initials = self._get_initials(a.first_name)
            formatted.append(f"{a.last_name}, {initials}")
        last = authors[-1]
        initials = self._get_initials(last.first_name)
        return ", ".join(formatted) + f", ... {last.last_name}, {initials}"

    def _format_authors_mla(self, authors: list[Author]) -> str:
        """Format authors in MLA style: Last, First, and First Last."""
        if not authors:
            return ""

        if len(authors) == 1:
            a = authors[0]
            return f"{a.last_name}, {a.first_name}"

        if len(authors) == 2:
            a1, a2 = authors[0], authors[1]
            return (
                f"{a1.last_name}, {a1.first_name}, and {a2.first_name} {a2.last_name}"
            )

        if len(authors) == 3:
            formatted = [f"{authors[0].last_name}, {authors[0].first_name}"]
            formatted.extend(f"{a.first_name} {a.last_name}" for a in authors[1:-1])
            formatted.append(f"and {authors[-1].first_name} {authors[-1].last_name}")
            return ", ".join(formatted)

        # More than 3 authors
        a = authors[0]
        return f"{a.last_name}, {a.first_name}, et al."

    def _format_authors_vancouver(self, authors: list[Author]) -> str:
        """Format authors in Vancouver style: Last FM, Last FM."""
        if not authors:
            return ""

        formatted = []
        for i, a in enumerate(authors):
            if i >= 6:
                formatted.append("et al.")
                break
            initials = self._get_initials(a.first_name, with_periods=False)
            formatted.append(f"{a.last_name} {initials}")

        return ", ".join(formatted)

    def _get_initials(self, first_name: str, with_periods: bool = True) -> str:
        """Get initials from first name(s)."""
        if not first_name:
            return ""
        parts = first_name.split()
        if with_periods:
            return " ".join(f"{p[0]}." for p in parts if p)
        return "".join(p[0] for p in parts if p)

    def _italicize(self, text: str) -> str:
        """Return text with markdown italics."""
        return f"*{text}*"

    # ==================== APA 7th Edition ====================

    def _format_apa7(self, source: ResearchSource) -> str:
        """Format citation in APA 7th edition style."""
        authors = self._format_authors_apa(self._get_authors(source))
        year = self._get_year(source)
        title = source.title

        if source.source_type == SourceType.JOURNAL_ARTICLE.value:
            journal = self._italicize(source.journal_name or "")
            volume = source.volume or ""
            issue = f"({source.issue})" if source.issue else ""
            pages = source.pages or ""
            doi = f"https://doi.org/{source.doi}" if source.doi else ""

            citation = f"{authors} ({year}). {title}. {journal}"
            if volume:
                citation += f", {volume}"
            if issue:
                citation += issue
            if pages:
                citation += f", {pages}"
            citation += "."
            if doi:
                citation += f" {doi}"
            return citation

        if source.source_type == SourceType.BOOK.value:
            publisher = source.publisher or ""
            citation = f"{authors} ({year}). {self._italicize(title)}. {publisher}."
            if source.doi:
                citation += f" https://doi.org/{source.doi}"
            return citation

        if source.source_type == SourceType.WEBSITE.value:
            access_date = source.access_date or datetime.now().strftime("%B %d, %Y")
            return f"{authors} ({year}). {title}. Retrieved {access_date}, from {source.url}"

        # Default format for other types
        return f"{authors} ({year}). {title}."

    def _in_text_apa7(self, source: ResearchSource) -> str:
        """Format in-text citation in APA style: (Author, Year)."""
        authors = self._get_authors(source)
        year = self._get_year(source)

        if not authors:
            # Use title if no authors
            short_title = (
                source.title[:30] + "..." if len(source.title) > 30 else source.title
            )
            return f'("{short_title}", {year})'

        if len(authors) == 1:
            return f"({authors[0].last_name}, {year})"

        if len(authors) == 2:
            return f"({authors[0].last_name} & {authors[1].last_name}, {year})"

        # 3+ authors
        return f"({authors[0].last_name} et al., {year})"

    # ==================== Harvard Style ====================

    def _format_harvard(self, source: ResearchSource) -> str:
        """Format citation in Harvard style (similar to APA but with some differences)."""
        # Harvard is very similar to APA
        authors = self._format_authors_apa(self._get_authors(source))
        year = self._get_year(source)
        title = source.title

        if source.source_type == SourceType.JOURNAL_ARTICLE.value:
            journal = self._italicize(source.journal_name or "")
            volume = source.volume or ""
            issue = f"({source.issue})" if source.issue else ""
            pages = source.pages or ""

            citation = f"{authors} ({year}) '{title}', {journal}"
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {source.issue}"
            if pages:
                citation += f", pp. {pages}"
            citation += "."
            return citation

        if source.source_type == SourceType.BOOK.value:
            publisher = source.publisher or ""
            return f"{authors} ({year}) {self._italicize(title)}, {publisher}."

        if source.source_type == SourceType.WEBSITE.value:
            access_date = source.access_date or datetime.now().strftime("%d %B %Y")
            return f"{authors} ({year}) {self._italicize(title)}, viewed {access_date}, <{source.url}>."

        return f"{authors} ({year}) '{title}'."

    def _in_text_harvard(self, source: ResearchSource) -> str:
        """Format in-text citation in Harvard style: (Author Year)."""
        authors = self._get_authors(source)
        year = self._get_year(source)

        if not authors:
            short_title = (
                source.title[:30] + "..." if len(source.title) > 30 else source.title
            )
            return f"({short_title} {year})"

        if len(authors) == 1:
            return f"({authors[0].last_name} {year})"

        if len(authors) == 2:
            return f"({authors[0].last_name} & {authors[1].last_name} {year})"

        return f"({authors[0].last_name} et al. {year})"

    # ==================== MLA Style ====================

    def _format_mla(self, source: ResearchSource) -> str:
        """Format citation in MLA 9th edition style."""
        authors = self._format_authors_mla(self._get_authors(source))
        title = source.title

        if source.source_type == SourceType.JOURNAL_ARTICLE.value:
            journal = self._italicize(source.journal_name or "")
            volume = source.volume or ""
            issue = source.issue or ""
            pages = source.pages or ""
            year = self._get_year(source)

            citation = f'{authors}. "{title}." {journal}'
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            citation += f", {year}"
            if pages:
                citation += f", pp. {pages}"
            citation += "."
            return citation

        if source.source_type == SourceType.BOOK.value:
            publisher = source.publisher or ""
            year = self._get_year(source)
            return f"{authors}. {self._italicize(title)}. {publisher}, {year}."

        if source.source_type == SourceType.WEBSITE.value:
            access_date = source.access_date or datetime.now().strftime("%d %b. %Y")
            return f'{authors}. "{title}." {self._italicize(source.url)}, Accessed {access_date}.'

        year = self._get_year(source)
        return f'{authors}. "{title}." {year}.'

    def _in_text_mla(self, source: ResearchSource) -> str:
        """Format in-text citation in MLA style: (Author Page)."""
        authors = self._get_authors(source)

        if not authors:
            short_title = (
                source.title[:30] + "..." if len(source.title) > 30 else source.title
            )
            return f'("{short_title}")'

        if len(authors) == 1:
            return f"({authors[0].last_name})"

        if len(authors) == 2:
            return f"({authors[0].last_name} and {authors[1].last_name})"

        return f"({authors[0].last_name} et al.)"

    # ==================== Chicago Style ====================

    def _format_chicago(self, source: ResearchSource) -> str:
        """Format citation in Chicago style (Notes-Bibliography)."""
        authors = self._format_authors_mla(self._get_authors(source))  # Similar format
        title = source.title
        year = self._get_year(source)

        if source.source_type == SourceType.JOURNAL_ARTICLE.value:
            journal = self._italicize(source.journal_name or "")
            volume = source.volume or ""
            issue = source.issue or ""
            pages = source.pages or ""

            citation = f'{authors}. "{title}." {journal}'
            if volume:
                citation += f" {volume}"
            if issue:
                citation += f", no. {issue}"
            citation += f" ({year})"
            if pages:
                citation += f": {pages}"
            citation += "."
            return citation

        if source.source_type == SourceType.BOOK.value:
            publisher = source.publisher or ""
            return f"{authors}. {self._italicize(title)}. {publisher}, {year}."

        return f'{authors}. "{title}." {year}.'

    def _in_text_chicago(self, source: ResearchSource) -> str:
        """Format in-text citation in Chicago style: (Author Year, Page)."""
        # Same as APA for author-date style
        return self._in_text_apa7(source)

    # ==================== IEEE Style ====================

    def _format_ieee(self, source: ResearchSource) -> str:
        """Format citation in IEEE style."""
        authors = self._format_authors_vancouver(self._get_authors(source))
        title = source.title
        year = self._get_year(source)

        if source.source_type == SourceType.JOURNAL_ARTICLE.value:
            journal = self._italicize(source.journal_name or "")
            volume = source.volume or ""
            issue = source.issue or ""
            pages = source.pages or ""

            citation = f'{authors}, "{title}," {journal}'
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            if pages:
                citation += f", pp. {pages}"
            citation += f", {year}."
            return citation

        if source.source_type == SourceType.BOOK.value:
            publisher = source.publisher or ""
            return f"{authors}, {self._italicize(title)}. {publisher}, {year}."

        if source.source_type == SourceType.WEBSITE.value:
            access_date = source.access_date or datetime.now().strftime("%b. %d, %Y")
            return f'{authors}, "{title}." [Online]. Available: {source.url}. [Accessed: {access_date}].'

        return f'{authors}, "{title}," {year}.'

    def _in_text_ieee(self, source: ResearchSource) -> str:
        """Format in-text citation in IEEE style: [N]."""
        # IEEE uses numbered citations, return placeholder
        return "[N]"

    # ==================== Vancouver Style ====================

    def _format_vancouver(self, source: ResearchSource) -> str:
        """Format citation in Vancouver style (used in medical/scientific)."""
        authors = self._format_authors_vancouver(self._get_authors(source))
        title = source.title
        year = self._get_year(source)

        if source.source_type == SourceType.JOURNAL_ARTICLE.value:
            journal = source.journal_name or ""
            volume = source.volume or ""
            issue = source.issue or ""
            pages = source.pages or ""

            citation = f"{authors}. {title}. {journal}. {year}"
            if volume:
                citation += f";{volume}"
            if issue:
                citation += f"({issue})"
            if pages:
                citation += f":{pages}"
            citation += "."
            return citation

        if source.source_type == SourceType.BOOK.value:
            publisher = source.publisher or ""
            return f"{authors}. {title}. {publisher}; {year}."

        if source.source_type == SourceType.WEBSITE.value:
            access_date = source.access_date or datetime.now().strftime("%Y %b %d")
            return f"{authors}. {title} [Internet]. Available from: {source.url}. Cited {access_date}."

        return f"{authors}. {title}. {year}."

    def _in_text_vancouver(self, source: ResearchSource) -> str:
        """Format in-text citation in Vancouver style: (N)."""
        # Vancouver uses numbered citations
        return "(N)"


# Global service instance
citation_service = CitationService()
