"""
Document structure analyzer for course content extraction
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from app.models import BloomLevel, ContentCategory, ContentType, OutcomeType
from app.services.pdf_parser_service import ExtractedDocument


class DocumentType(str, Enum):
    """Types of course documents"""

    UNIT_OUTLINE = "unit_outline"
    LECTURE_NOTES = "lecture_notes"
    TUTORIAL_GUIDE = "tutorial_guide"
    ASSIGNMENT_BRIEF = "assignment_brief"
    READING_LIST = "reading_list"
    SYLLABUS = "syllabus"
    STUDY_GUIDE = "study_guide"
    UNKNOWN = "unknown"


@dataclass
class AnalyzedSection:
    """Analyzed document section"""

    title: str
    content: str
    section_type: str  # heading, paragraph, list, table, etc.
    level: int  # Heading level or nesting depth
    page_start: int
    page_end: int
    word_count: int
    metadata: dict[str, Any] | None = None


@dataclass
class ExtractedLearningOutcome:
    """Extracted learning outcome"""

    text: str
    outcome_type: OutcomeType
    bloom_level: BloomLevel | None = None
    verbs: list[str] | None = None
    topics: list[str] | None = None


@dataclass
class ExtractedAssessment:
    """Extracted assessment information"""

    name: str
    assessment_type: str
    weight: float | None = None
    due_week: int | None = None
    description: str | None = None
    requirements: list[str] | None = None


@dataclass
class ExtractedWeeklyContent:
    """Extracted weekly content"""

    week_number: int
    topic: str
    pre_class: list[str] | None = None
    in_class: list[str] | None = None
    post_class: list[str] | None = None
    readings: list[str] | None = None
    activities: list[str] | None = None


@dataclass
class DocumentAnalysis:
    """Complete document analysis result"""

    document_type: DocumentType
    title: str | None
    sections: list[AnalyzedSection]
    learning_outcomes: list[ExtractedLearningOutcome]
    assessments: list[ExtractedAssessment]
    weekly_content: list[ExtractedWeeklyContent]
    key_concepts: list[str]
    prerequisites: list[str]
    references: list[str]
    metadata: dict[str, Any]


class DocumentAnalyzerService:
    """Service for analyzing document structure and extracting course content"""

    # Bloom's taxonomy verb mapping
    BLOOM_VERBS: ClassVar[dict[BloomLevel, list[str]]] = {
        BloomLevel.REMEMBER: [
            "identify",
            "list",
            "name",
            "state",
            "describe",
            "recall",
            "recognize",
            "label",
            "select",
            "match",
        ],
        BloomLevel.UNDERSTAND: [
            "explain",
            "summarize",
            "paraphrase",
            "classify",
            "compare",
            "contrast",
            "discuss",
            "interpret",
            "illustrate",
            "predict",
        ],
        BloomLevel.APPLY: [
            "apply",
            "demonstrate",
            "implement",
            "solve",
            "use",
            "execute",
            "carry out",
            "practice",
            "calculate",
            "complete",
        ],
        BloomLevel.ANALYZE: [
            "analyze",
            "examine",
            "investigate",
            "differentiate",
            "organize",
            "deconstruct",
            "evaluate",
            "test",
            "diagnose",
            "inspect",
        ],
        BloomLevel.EVALUATE: [
            "evaluate",
            "assess",
            "critique",
            "judge",
            "justify",
            "defend",
            "argue",
            "prioritize",
            "rate",
            "select",
        ],
        BloomLevel.CREATE: [
            "create",
            "design",
            "develop",
            "construct",
            "produce",
            "generate",
            "plan",
            "invent",
            "compose",
            "formulate",
        ],
    }

    async def analyze_document(self, document: ExtractedDocument) -> DocumentAnalysis:
        """
        Analyze document structure and extract course content

        Args:
            document: Extracted PDF document

        Returns:
            Complete document analysis
        """
        # Determine document type
        doc_type = self._identify_document_type(document)

        # Extract sections
        sections = self._extract_sections(document)

        # Extract learning outcomes
        learning_outcomes = self._extract_learning_outcomes(document)

        # Extract assessments
        assessments = self._extract_assessments(document)

        # Extract weekly content
        weekly_content = self._extract_weekly_content(document)

        # Extract key concepts
        key_concepts = self._extract_key_concepts(document)

        # Extract prerequisites
        prerequisites = self._extract_prerequisites(document)

        # Extract references
        references = self._extract_references(document)

        return DocumentAnalysis(
            document_type=doc_type,
            title=document.metadata.title or self._extract_title(document),
            sections=sections,
            learning_outcomes=learning_outcomes,
            assessments=assessments,
            weekly_content=weekly_content,
            key_concepts=key_concepts,
            prerequisites=prerequisites,
            references=references,
            metadata={
                "page_count": document.metadata.page_count,
                "has_toc": bool(document.toc),
                "extraction_method": document.extraction_method,
                "word_count": len(document.full_text.split()),
            },
        )

    def _identify_document_type(self, document: ExtractedDocument) -> DocumentType:  # noqa: PLR0911
        """Identify the type of course document"""
        text_lower = document.full_text.lower()
        title_lower = (document.metadata.title or "").lower()

        # Check for specific document types
        if "unit outline" in text_lower or "unit outline" in title_lower:
            return DocumentType.UNIT_OUTLINE
        if "lecture" in title_lower or "lecture notes" in text_lower:
            return DocumentType.LECTURE_NOTES
        if "tutorial" in title_lower or "tutorial guide" in text_lower:
            return DocumentType.TUTORIAL_GUIDE
        if "assignment" in title_lower or "assignment brief" in text_lower:
            return DocumentType.ASSIGNMENT_BRIEF
        if "reading list" in text_lower or "bibliography" in text_lower:
            return DocumentType.READING_LIST
        if "syllabus" in title_lower or "course syllabus" in text_lower:
            return DocumentType.SYLLABUS
        if "study guide" in title_lower:
            return DocumentType.STUDY_GUIDE
        return DocumentType.UNKNOWN

    def _extract_title(self, document: ExtractedDocument) -> str | None:
        """Extract document title from content"""
        if document.metadata.title:
            return document.metadata.title

        # Try to find title in first page
        if document.pages:
            first_page = document.pages[0].text
            lines = first_page.split("\n")[:10]  # Check first 10 lines

            for text_line in lines:
                line = text_line.strip()
                # Look for lines that might be titles
                if (
                    line
                    and len(line) > 10
                    and len(line) < 200
                    and (line.isupper() or line.istitle())
                ):
                    return line

        return None

    def _extract_sections(self, document: ExtractedDocument) -> list[AnalyzedSection]:
        """Extract document sections with hierarchy"""
        sections = []

        # Use TOC if available
        if document.toc:
            for item in document.toc:
                # Find section content in pages
                start_page = item["page"]
                section_text = self._extract_section_text(
                    document, item["title"], start_page
                )

                sections.append(
                    AnalyzedSection(
                        title=item["title"],
                        content=section_text,
                        section_type="heading",
                        level=item["level"],
                        page_start=start_page,
                        page_end=start_page,  # Will be updated
                        word_count=len(section_text.split()),
                    )
                )
        else:
            # Extract sections using pattern matching
            sections = self._extract_sections_by_pattern(document)

        return sections

    def _extract_section_text(
        self, document: ExtractedDocument, title: str, start_page: int
    ) -> str:
        """Extract text for a specific section"""
        section_text = []
        found_section = False

        for page in document.pages[start_page - 1 :]:
            if title.lower() in page.text.lower():
                found_section = True

            if found_section:
                section_text.append(page.text)

                # Stop if we hit another major heading
                if self._is_major_heading(page.text) and page.page_number > start_page:
                    break

        return "\n".join(section_text)

    def _is_major_heading(self, text: str) -> bool:
        """Check if text contains a major heading"""
        heading_patterns = [
            r"^(Chapter|Section|Unit|Module|Week)\s+\d+",
            r"^(Introduction|Conclusion|References|Bibliography|Appendix)",
            r"^Learning\s+Outcomes?",
            r"^Assessment",
        ]

        for pattern in heading_patterns:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                return True

        return False

    def _extract_sections_by_pattern(
        self, document: ExtractedDocument
    ) -> list[AnalyzedSection]:
        """Extract sections using pattern matching"""
        sections = []
        current_section = None
        current_content = []

        for page in document.pages:
            lines = page.text.split("\n")

            for text_line in lines:
                line = text_line.strip()

                if self._is_section_heading(line):
                    # Save previous section
                    if current_section:
                        current_section.content = "\n".join(current_content)
                        current_section.word_count = len(
                            current_section.content.split()
                        )
                        sections.append(current_section)

                    # Start new section
                    current_section = AnalyzedSection(
                        title=line,
                        content="",
                        section_type="heading",
                        level=self._get_heading_level(line),
                        page_start=page.page_number,
                        page_end=page.page_number,
                        word_count=0,
                    )
                    current_content = []
                elif current_section:
                    current_content.append(line)
                    current_section.page_end = page.page_number

        # Save last section
        if current_section:
            current_section.content = "\n".join(current_content)
            current_section.word_count = len(current_section.content.split())
            sections.append(current_section)

        return sections

    def _is_section_heading(self, text: str) -> bool:
        """Check if text is a section heading"""
        if not text or len(text) < 3:
            return False

        # Check for common heading patterns
        patterns = [
            r"^\d+\.?\s+",  # Numbered sections
            r"^[A-Z][A-Z\s]+$",  # All caps
            r"^(Chapter|Section|Unit|Module|Week|Topic)\s+",
            r"^(Introduction|Overview|Objectives|Outcomes|Assessment|Summary|Conclusion)",
        ]

        return any(re.match(pattern, text, re.IGNORECASE) for pattern in patterns)

    def _get_heading_level(self, text: str) -> int:
        """Determine heading level (1-6)"""
        if re.match(r"^(Chapter|Unit)\s+", text, re.IGNORECASE):
            return 1
        if re.match(r"^(Section|Module)\s+", text, re.IGNORECASE):
            return 2
        if re.match(r"^(Week|Topic)\s+", text, re.IGNORECASE) or re.match(
            r"^\d+\.\d+\.\d+", text
        ):
            return 3
        if re.match(r"^\d+\.\d+", text):
            return 2
        if re.match(r"^\d+\.?\s+", text):
            return 1
        return 2  # Default

    def _extract_learning_outcomes(
        self, document: ExtractedDocument
    ) -> list[ExtractedLearningOutcome]:
        """Extract learning outcomes from document"""
        outcomes = []
        text = document.full_text

        # Patterns for finding learning outcomes sections
        lo_section_patterns = [
            r"Learning\s+Outcomes?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Course\s+Outcomes?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Unit\s+Outcomes?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Objectives?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Upon\s+completion.*?will\s+be\s+able\s+to[:\s]*(.*?)(?=\n\n|\Z)",
        ]

        for pattern in lo_section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section_text = match.group(1)
                # Extract individual outcomes
                outcome_lines = self._extract_list_items(section_text)

                for line in outcome_lines:
                    if len(line) > 10:  # Filter out very short lines
                        outcome = self._parse_learning_outcome(line)
                        if outcome:
                            outcomes.append(outcome)

        return outcomes

    def _extract_list_items(self, text: str) -> list[str]:
        """Extract list items from text"""
        items = []

        # Common list patterns
        patterns = [
            r"^\s*[-•*]\s*(.+)$",  # Bullet points
            r"^\s*\d+[\.)]\s*(.+)$",  # Numbered lists
            r"^\s*[a-z][\.)]\s*(.+)$",  # Lettered lists
        ]

        lines = text.split("\n")
        for line in lines:
            for pattern in patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    items.append(match.group(1).strip())
                    break
            else:
                # If no pattern matches but line looks like content
                if line.strip() and not line.strip().endswith(":"):
                    items.append(line.strip())

        return items

    def _parse_learning_outcome(self, text: str) -> ExtractedLearningOutcome | None:
        """Parse a learning outcome from text"""
        if not text or len(text) < 10:
            return None

        # Determine outcome type
        outcome_type = OutcomeType.ULO  # Default
        if "course" in text.lower():
            outcome_type = OutcomeType.CLO
        elif "week" in text.lower():
            outcome_type = OutcomeType.WLO

        # Extract verbs and determine Bloom's level
        verbs = []
        bloom_level = None

        for level, verb_list in self.BLOOM_VERBS.items():
            for verb in verb_list:
                if verb in text.lower():
                    verbs.append(verb)
                    if not bloom_level:
                        bloom_level = level

        # Extract topics (nouns and noun phrases)
        topics = self._extract_topics(text)

        return ExtractedLearningOutcome(
            text=text,
            outcome_type=outcome_type,
            bloom_level=bloom_level,
            verbs=verbs,
            topics=topics,
        )

    def _extract_topics(self, text: str) -> list[str]:
        """Extract key topics from text"""
        # Simple topic extraction - look for capitalized words and phrases
        topics = []

        # Find capitalized phrases
        cap_pattern = r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*"
        matches = re.findall(cap_pattern, text)

        for match in matches:
            if len(match) > 3 and match not in topics:
                topics.append(match)

        return topics[:5]  # Limit to 5 topics

    def _extract_assessments(
        self, document: ExtractedDocument
    ) -> list[ExtractedAssessment]:
        """Extract assessment information"""
        assessments = []
        text = document.full_text

        # Find assessment sections
        assessment_patterns = [
            r"Assessment[s]?\s*[:\s]*(.*?)(?=\n\n|\Z)",
            r"Assignment[s]?\s*[:\s]*(.*?)(?=\n\n|\Z)",
            r"Exam[s]?\s*[:\s]*(.*?)(?=\n\n|\Z)",
            r"Quiz[zes]?\s*[:\s]*(.*?)(?=\n\n|\Z)",
        ]

        for pattern in assessment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section_text = match.group(1)
                # Parse assessment details
                assessment = self._parse_assessment(section_text)
                if assessment:
                    assessments.append(assessment)

        return assessments

    def _parse_assessment(self, text: str) -> ExtractedAssessment | None:
        """Parse assessment details from text"""
        if not text:
            return None

        # Extract assessment name
        name = "Assessment"
        name_match = re.search(
            r"(Assignment|Quiz|Exam|Test|Project)\s*\d*", text, re.IGNORECASE
        )
        if name_match:
            name = name_match.group()

        # Extract weight/percentage
        weight = None
        weight_match = re.search(r"(\d+)\s*%", text)
        if weight_match:
            weight = float(weight_match.group(1))

        # Extract week number
        due_week = None
        week_match = re.search(r"Week\s*(\d+)", text, re.IGNORECASE)
        if week_match:
            due_week = int(week_match.group(1))

        # Determine assessment type
        assessment_type = "assignment"
        if "quiz" in text.lower():
            assessment_type = "quiz"
        elif "exam" in text.lower():
            assessment_type = "exam"
        elif "project" in text.lower():
            assessment_type = "project"
        elif "presentation" in text.lower():
            assessment_type = "presentation"

        return ExtractedAssessment(
            name=name,
            assessment_type=assessment_type,
            weight=weight,
            due_week=due_week,
            description=text[:500],  # First 500 chars as description
        )

    def _extract_weekly_content(
        self, document: ExtractedDocument
    ) -> list[ExtractedWeeklyContent]:
        """Extract weekly content schedule"""
        weekly_content = []
        text = document.full_text

        # Find weekly sections
        week_pattern = r"Week\s+(\d+)[:\s]*([^\n]*)\n(.*?)(?=Week\s+\d+|\Z)"
        matches = re.finditer(week_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            week_num = int(match.group(1))
            topic = match.group(2).strip()
            content = match.group(3)

            # Parse weekly activities
            weekly = ExtractedWeeklyContent(
                week_number=week_num,
                topic=topic if topic else f"Week {week_num}",
            )

            # Extract pre-class, in-class, post-class activities
            if "pre-class" in content.lower() or "before class" in content.lower():
                weekly.pre_class = self._extract_activities(content, "pre-class")

            if "in-class" in content.lower() or "during class" in content.lower():
                weekly.in_class = self._extract_activities(content, "in-class")

            if "post-class" in content.lower() or "after class" in content.lower():
                weekly.post_class = self._extract_activities(content, "post-class")

            # Extract readings
            if "reading" in content.lower():
                weekly.readings = self._extract_readings(content)

            weekly_content.append(weekly)

        return weekly_content

    def _extract_activities(self, text: str, activity_type: str) -> list[str]:
        """Extract activities from text"""
        activities = []

        # Find activity section
        pattern = rf"{activity_type}[:\s]*(.*?)(?=\n\n|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            section = match.group(1)
            activities = self._extract_list_items(section)

        return activities

    def _extract_readings(self, text: str) -> list[str]:
        """Extract reading materials"""
        readings = []

        # Find readings section
        pattern = r"Reading[s]?[:\s]*(.*?)(?=\n\n|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            section = match.group(1)
            readings = self._extract_list_items(section)

        return readings

    def _extract_key_concepts(self, document: ExtractedDocument) -> list[str]:
        """Extract key concepts from document"""
        concepts = []
        text = document.full_text

        # Look for key concepts sections
        patterns = [
            r"Key\s+Concepts?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Important\s+Terms?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Vocabulary[:\s]*(.*?)(?=\n\n|\Z)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section = match.group(1)
                items = self._extract_list_items(section)
                concepts.extend(items)

        # Remove duplicates
        return list(set(concepts))[:20]  # Limit to 20 concepts

    def _extract_prerequisites(self, document: ExtractedDocument) -> list[str]:
        """Extract prerequisites"""
        prerequisites = []
        text = document.full_text

        # Look for prerequisites sections
        patterns = [
            r"Prerequisites?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Required\s+Knowledge[:\s]*(.*?)(?=\n\n|\Z)",
            r"Prior\s+Learning[:\s]*(.*?)(?=\n\n|\Z)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section = match.group(1)
                items = self._extract_list_items(section)
                prerequisites.extend(items)

        return prerequisites

    def _extract_references(self, document: ExtractedDocument) -> list[str]:
        """Extract references and bibliography"""
        references = []
        text = document.full_text

        # Look for reference sections
        patterns = [
            r"References?[:\s]*(.*?)(?=\n\n|\Z)",
            r"Bibliography[:\s]*(.*?)(?=\n\n|\Z)",
            r"Further\s+Reading[:\s]*(.*?)(?=\n\n|\Z)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section = match.group(1)
                # Extract references (look for author-year patterns)
                ref_pattern = r"([A-Z][a-z]+(?:,?\s+[A-Z]\.?)*)\s*\((\d{4})\)"
                ref_matches = re.findall(ref_pattern, section)
                for author, year in ref_matches:
                    references.append(f"{author} ({year})")

                # Also extract full reference lines
                lines = section.split("\n")
                references.extend(
                    line.strip()
                    for line in lines
                    if len(line) > 20 and "(" in line and ")" in line
                )

        # Remove duplicates
        return list(set(references))[:30]  # Limit to 30 references

    async def map_to_course_structure(
        self, analysis: DocumentAnalysis
    ) -> dict[str, Any]:
        """
        Map analyzed document to course structure models

        Args:
            analysis: Document analysis result

        Returns:
            Mapping to course structure models
        """
        mapping = {
            "course_outline": {
                "title": analysis.title,
                "description": self._generate_description(analysis),
                "duration_weeks": len(analysis.weekly_content)
                if analysis.weekly_content
                else 12,
            },
            "learning_outcomes": [],
            "weekly_topics": [],
            "assessments": [],
            "content_suggestions": [],
        }

        # Map learning outcomes
        for outcome in analysis.learning_outcomes:
            mapping["learning_outcomes"].append(
                {
                    "outcome_type": outcome.outcome_type,
                    "outcome_text": outcome.text,
                    "bloom_level": outcome.bloom_level.value
                    if outcome.bloom_level
                    else None,
                }
            )

        # Map weekly topics
        for weekly in analysis.weekly_content:
            topic_data = {
                "week_number": weekly.week_number,
                "topic_title": weekly.topic,
                "pre_class_modules": self._format_activities(weekly.pre_class),
                "in_class_activities": self._format_activities(weekly.in_class),
                "post_class_tasks": self._format_activities(weekly.post_class),
                "required_readings": self._format_readings(weekly.readings),
            }
            mapping["weekly_topics"].append(topic_data)

        # Map assessments
        for assessment in analysis.assessments:
            mapping["assessments"].append(
                {
                    "assessment_name": assessment.name,
                    "assessment_type": assessment.assessment_type,
                    "weight_percentage": assessment.weight,
                    "due_week": assessment.due_week,
                    "description": assessment.description,
                }
            )

        # Generate content suggestions based on document type
        mapping["content_suggestions"] = self._generate_content_suggestions(analysis)

        return mapping

    def _generate_description(self, analysis: DocumentAnalysis) -> str:
        """Generate course description from analysis"""
        parts = []

        if analysis.title:
            parts.append(f"Course: {analysis.title}")

        if analysis.learning_outcomes:
            parts.append(
                f"This course covers {len(analysis.learning_outcomes)} learning outcomes"
            )

        if analysis.weekly_content:
            parts.append(f"spanning {len(analysis.weekly_content)} weeks")

        if analysis.key_concepts:
            concepts_preview = ", ".join(analysis.key_concepts[:5])
            parts.append(f"Key concepts include: {concepts_preview}")

        return ". ".join(parts) if parts else "Course content extracted from document"

    def _format_activities(self, activities: list[str] | None) -> list[dict[str, Any]]:
        """Format activities for storage"""
        if not activities:
            return []

        return [
            {"title": activity[:100], "description": activity, "duration_minutes": 30}
            for activity in activities
        ]

    def _format_readings(self, readings: list[str] | None) -> list[dict[str, str]]:
        """Format readings for storage"""
        if not readings:
            return []

        return [{"title": reading[:200], "type": "required"} for reading in readings]

    def _generate_content_suggestions(
        self, analysis: DocumentAnalysis
    ) -> list[dict[str, Any]]:
        """Generate content creation suggestions based on analysis"""
        suggestions = []

        # Suggest content based on document type
        if analysis.document_type == DocumentType.UNIT_OUTLINE:
            suggestions.append(
                {
                    "type": ContentType.SYLLABUS.value,
                    "title": "Course Syllabus",
                    "category": ContentCategory.GENERAL.value,
                    "reason": "Unit outline detected - syllabus needed",
                }
            )
            suggestions.append(
                {
                    "type": ContentType.SCHEDULE.value,
                    "title": "Weekly Schedule",
                    "category": ContentCategory.GENERAL.value,
                    "reason": "Create detailed weekly schedule from outline",
                }
            )

        # Suggest content for each week
        for weekly in analysis.weekly_content:
            suggestions.append(
                {
                    "type": ContentType.LECTURE.value,
                    "title": f"Week {weekly.week_number}: {weekly.topic}",
                    "week_number": weekly.week_number,
                    "category": ContentCategory.PRE_CLASS.value,
                    "reason": f"Lecture content for week {weekly.week_number}",
                }
            )

            if weekly.in_class:
                suggestions.append(
                    {
                        "type": ContentType.WORKSHEET.value,
                        "title": f"Week {weekly.week_number} Activities",
                        "week_number": weekly.week_number,
                        "category": ContentCategory.IN_CLASS.value,
                        "reason": "In-class activities detected",
                    }
                )

        # Suggest assessment content
        suggestions.extend(
            {
                "type": ContentType.ASSIGNMENT.value,
                "title": assessment.name,
                "week_number": assessment.due_week,
                "category": ContentCategory.POST_CLASS.value,
                "reason": f"Assessment: {assessment.assessment_type}",
            }
            for assessment in analysis.assessments
        )

        return suggestions


# Singleton instance
document_analyzer_service = DocumentAnalyzerService()
