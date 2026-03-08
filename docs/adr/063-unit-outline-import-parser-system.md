# 063. Unit Outline Import with Pluggable Parser System

Date: 2026-03-09

## Status

Accepted

## Context

The application currently offers three paths to create a unit: manual entry, AI scaffold (with optional research sources), and LMS package import (IMSCC/SCORM/ZIP). A common real-world starting point is missing: the **institutional unit outline** — a structured document (typically PDF, sometimes DOCX or TXT) that every university publishes for each unit. These outlines contain unit metadata, learning outcomes, weekly schedules, assessments, textbooks, and institutional policies.

Key challenges:

1. **Format variation** — Every institution uses a different outline template. Curtin University's format differs from UWA's, which differs from a K-12 school's lesson plan or an executive education programme brief.
2. **Document format** — Outlines may be PDF, DOCX, or even plain text.
3. **Partial relevance** — Outlines contain both course-authoring data (schedule, ULOs, assessments) and institutional policy (academic integrity, special consideration) that doesn't map to our data model.
4. **Accuracy trade-off** — A generic parser works everywhere but with lower precision; an institution-specific parser is more accurate but only works for one format.

The existing file import system (ADR-023) handles material upload (individual PDFs, PPTX, etc.) but doesn't extract structured unit metadata from outline documents.

## Decision

Implement a **pluggable outline parser system** with a generic LLM-powered default and support for institution-specific parsers.

### Architecture

```
backend/app/services/outline_parsers/
├── __init__.py              # Registry + factory (get_parser, list_parsers)
├── base.py                  # OutlineParser ABC + OutlineParseResult schema
├── generic_parser.py        # LLM-powered, handles any format/institution
└── curtin_parser.py         # Curtin University (regex + known section headings)
```

### Parser Interface

Each parser implements:

```python
class OutlineParser(ABC):
    name: str                          # e.g. "generic", "curtin"
    display_name: str                  # e.g. "Generic (AI-Powered)", "Curtin University"
    description: str
    supported_formats: list[str]       # e.g. ["pdf", "docx", "txt"]

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        user_context: dict | None = None,  # sector, preferences
    ) -> OutlineParseResult: ...
```

### Extraction Schema (OutlineParseResult)

```python
class OutlineParseResult(BaseModel):
    # Unit metadata
    unit_code: str | None
    unit_title: str | None
    description: str | None
    credit_points: int | None
    duration_weeks: int | None
    year: int | None
    semester: str | None
    prerequisites: str | None
    delivery_mode: str | None
    teaching_pattern: str | None

    # Structured data
    learning_outcomes: list[ExtractedULO]
    weekly_schedule: list[ExtractedWeek]
    assessments: list[ExtractedAssessment]
    textbooks: list[ExtractedTextbook]

    # Unmapped content
    supplementary_info: list[ExtractedSnippet]

    # Metadata
    confidence: float          # 0.0–1.0
    parser_used: str
    warnings: list[str]
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/import/outline/parsers` | GET | List available parsers |
| `/api/import/outline/parse` | POST | Upload + parse document |
| `/api/import/outline/apply` | POST | Create unit from reviewed extraction |

### User Flow

1. User clicks "Create from Outline" on the dashboard
2. Uploads a document (PDF/DOCX/TXT) and selects a parser (defaults to Generic)
3. Backend parses the document and returns `OutlineParseResult`
4. Frontend displays an editable review form: unit details, ULOs, weekly schedule, assessments, textbooks, and supplementary info (with keep/drop toggles)
5. User edits/corrects the extraction and clicks "Create Unit"
6. Backend creates Unit + ULOs + WeeklyTopics + Assessments from the reviewed data

### Generic vs Institution-Specific Parsers

| Aspect | Generic Parser | Institution Parser (e.g. Curtin) |
|--------|---------------|----------------------------------|
| Method | LLM extraction (document text → structured JSON prompt) | Regex + known section headings |
| Accuracy | Good for any format, moderate precision | High precision for known format |
| Cost | LLM API call required | Free (no API call) |
| Fallback | N/A — is the fallback | Falls back to generic on failure |

### Unmapped Content Handling

Content that doesn't map to our data model (policies, special requirements, graduate attributes text, etc.) is returned in `supplementary_info` as `ExtractedSnippet` items (section heading + content text). In the review form, users can:

- **Keep** → stored in `unit_metadata["supplementary_info"]` as reference notes
- **Drop** → discarded

This avoids polluting structured data while preserving potentially useful context for the educator.

### Textbook Storage

Textbooks are stored in `unit_metadata["textbooks"]` as a JSON list (title, authors, isbn, required/recommended). No dedicated model — textbooks are reference info, not core authoring data.

## Consequences

### Positive

- Covers the most common real-world starting point (institutional outline document)
- Plugin architecture allows institution-specific parsers without touching core code
- Generic LLM parser works for any institution, any format, any sector
- Review/edit step ensures the user controls what gets imported (ADR-040 ambient context pattern)
- Reuses existing text extraction services (`pdf_parser_service`, `file_import_service`)
- Supplementary info capture preserves context without polluting the data model

### Negative

- Generic parser requires an LLM API call (cost per import)
- Institution-specific parsers need maintenance when outline formats change
- LLM extraction accuracy varies with document quality (scanned PDFs, complex layouts)

### Neutral

- Each institution parser is a separate Python module — easy to add, but requires code deployment (no runtime upload in v1)
- Textbooks stored as JSON in unit_metadata rather than a dedicated model — simpler but less queryable
- Confidence score is informational only — no automatic accept/reject threshold

## Alternatives Considered

### Single monolithic parser with institution config files

- One parser class with YAML/JSON config files defining section headings per institution
- Rejected: too rigid for the variety of outline formats; regex patterns alone can't handle the structural diversity; institution parsers may need fundamentally different extraction strategies

### Template-matching / OCR approach

- Use computer vision to match outline layouts against known templates
- Rejected: over-engineered for v1; PDF text extraction handles most cases; vision API can be a future enhancement for scanned documents

### No institution-specific parsers — LLM only

- Just ship the generic LLM parser and skip institution-specific ones
- Rejected: deterministic parsers are faster, cheaper, and more accurate for known formats; the hybrid approach gives the best of both worlds

### Dedicated Textbook model

- Create a `Textbook` SQLAlchemy model with relationships
- Rejected for now: textbooks are reference metadata, not core authoring data; JSON storage in `unit_metadata` is simpler and sufficient; can be promoted to a model later if needed

## Implementation Notes

- Text extraction reuses `pdf_parser_service.extract_text()` and `file_import_service` for DOCX/TXT
- Generic parser prompt should be structured to return JSON matching `OutlineParseResult`, using the structured output retry pattern (ADR-045)
- Curtin parser targets their standard sections: "Unit Learning Outcomes", "Assessment Summary", "Unit Schedule/Teaching Schedule", "Prescribed Text", "Recommended Reading"
- Frontend review form follows the same propose/review/apply pattern as research scaffold (ADR-039)
- Parser registry uses a simple dict — no dynamic discovery needed for v1
- Future: admin parser management (download template → edit → upload) tracked in IDEAS.md

## References

- [ADR-023: File Import and Processing Architecture](023-file-import-processing-architecture.md)
- [ADR-039: Tiered Research Architecture with Propose/Apply](039-tiered-research-architecture.md)
- [ADR-040: Ambient Context — Best Guess + Human Override](040-ambient-context-pattern.md)
- [ADR-045: Structured LLM Output with Retry Loop](045-structured-llm-output-retry.md)
- [ADR-061: Transparent Import Reporting](061-transparent-import-reporting.md)
