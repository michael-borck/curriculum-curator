# Unit Outline Import — Implementation Plan

> Tracking document for the outline import feature (ADR-063).
> Check off steps as they are completed.

## Overview

A 4th unit creation pathway: upload an institutional unit outline document (PDF, DOCX, TXT) → parser extracts structured data → user reviews/edits extraction → system scaffolds the unit.

## Implementation Steps

### Phase 1: Backend Parser System

- [x] **1.1** Create `backend/app/services/outline_parsers/__init__.py` — parser registry (`get_parser`, `list_parsers`)
- [x] **1.2** Create `backend/app/services/outline_parsers/base.py` — `OutlineParser` ABC + all data classes (`OutlineParseResult`, `ExtractedULO`, `ExtractedWeek`, `ExtractedAssessment`, `ExtractedTextbook`, `ExtractedSnippet`)
- [x] **1.3** Create `backend/app/services/outline_parsers/generic_parser.py` — LLM-powered generic parser
- [x] **1.4** Create `backend/app/services/outline_parsers/curtin_parser.py` — Curtin University regex-based parser

### Phase 2: Backend API

- [x] **2.1** Create `backend/app/schemas/outline_import.py` — request/response schemas (`OutlineParseResponse`, `OutlineApplyRequest`, `ParserInfo`)
- [x] **2.2** Create `backend/app/api/routes/outline_import.py` — three endpoints: `GET /parsers`, `POST /parse`, `POST /apply`
- [x] **2.3** Register route in `backend/app/main.py`

### Phase 3: Frontend

- [x] **3.1** Create `frontend/src/services/outlineImportApi.ts` — API client
- [x] **3.2** Create `frontend/src/features/import/OutlineImport.tsx` — upload + parser select + orchestration
- [x] **3.3** Create `frontend/src/features/import/OutlineReviewForm.tsx` — editable review form (unit details, ULOs, schedule, assessments, textbooks, supplementary info)
- [x] **3.4** Wire into `DashboardPage.tsx` — add "Create from Outline" as a creation option

### Phase 4: Tests & Quality

- [x] **4.1** Create `backend/tests/test_outline_parsers.py` — unit tests for parsers (32 tests)
- [x] **4.2** Run all linters and type checkers (ruff, basedpyright, eslint, tsc)
- [ ] **4.3** Manual end-to-end test with a real Curtin outline PDF

### Phase 5: Documentation (Done)

- [x] **5.1** Write ADR-063
- [x] **5.2** Update user stories (1.13–1.15, 6.9–6.10)
- [x] **5.3** Update acceptance tests (Scenario 16)
- [x] **5.4** Update IDEAS.md with future parser management notes

## Key Files

### New Files
| File | Purpose |
|------|---------|
| `backend/app/services/outline_parsers/__init__.py` | Parser registry |
| `backend/app/services/outline_parsers/base.py` | Abstract base + data classes |
| `backend/app/services/outline_parsers/generic_parser.py` | LLM-powered generic parser |
| `backend/app/services/outline_parsers/curtin_parser.py` | Curtin-specific parser |
| `backend/app/schemas/outline_import.py` | API schemas |
| `backend/app/api/routes/outline_import.py` | API routes |
| `frontend/src/services/outlineImportApi.ts` | Frontend API client |
| `frontend/src/features/import/OutlineImport.tsx` | Upload + parser select UI |
| `frontend/src/features/import/OutlineReviewForm.tsx` | Review/edit form |
| `backend/tests/test_outline_parsers.py` | Parser tests |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/main.py` | Register outline import router |
| `frontend/src/pages/DashboardPage.tsx` | Add "Create from Outline" option |
| `docs/user-stories.md` | Stories 1.13–1.15, 6.9–6.10 |
| `docs/acceptance-tests.md` | Scenario 16 |
| `docs/IDEAS.md` | Future parser management notes |
| `docs/adr/index.md` | Add ADR-063 |

## Architecture

```
Upload Document → Select Parser → POST /parse
                                      ↓
                              OutlineParseResult
                                      ↓
                           Review Form (editable)
                                      ↓
                     User approves → POST /apply
                                      ↓
                    Unit + ULOs + WeeklyTopics + Assessments
                    + textbooks in unit_metadata
                    + supplementary_info in unit_metadata
```

## Parser Plugin Interface

```python
class OutlineParser(ABC):
    name: str
    display_name: str
    description: str
    supported_formats: list[str]

    async def parse(self, file_content, filename, file_type, user_context) -> OutlineParseResult
```

## Design Decisions

- **Textbooks** → `unit_metadata["textbooks"]` (JSON, no dedicated model)
- **Supplementary info** → `unit_metadata["supplementary_info"]` (kept items only)
- **Parser fallback** → institution parsers fall back to generic on failure
- **Review pattern** → same propose/review/apply as research scaffold (ADR-039)
- **No runtime parser upload** in v1 — future feature tracked in IDEAS.md
