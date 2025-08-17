# Task List: Curriculum Curator MVP Implementation

## Relevant Files

- `backend/app/models/course.py` - SQLAlchemy models for courses, modules, and LRDs
- `backend/app/models/course.test.py` - Unit tests for course models
- `backend/app/models/material.py` - Models for content materials and versions
- `backend/app/models/material.test.py` - Unit tests for material models
- `backend/app/models/conversation.py` - Models for conversation history
- `backend/app/api/routes/lrd.py` - API endpoints for LRD management
- `backend/app/api/routes/lrd.test.py` - Integration tests for LRD endpoints
- `backend/app/api/routes/materials.py` - API endpoints for material generation
- `backend/app/api/routes/materials.test.py` - Integration tests for material endpoints
- `backend/app/schemas/lrd.py` - Pydantic schemas for LRD data
- `backend/app/schemas/material.py` - Pydantic schemas for materials
- `backend/app/services/lrd_service.py` - Business logic for LRD operations
- `backend/app/services/lrd_service.test.py` - Unit tests for LRD service
- `backend/app/services/content_generator.py` - Content generation orchestration
- `backend/app/services/content_generator.test.py` - Unit tests for content generator
- `backend/app/services/import_service.py` - File import and processing
- `backend/app/services/import_service.test.py` - Unit tests for import service
- `backend/app/services/version_control.py` - Version management for materials
- `backend/app/plugins/validators/readability.py` - Readability validator implementation
- `backend/app/plugins/validators/structure.py` - Structure validator implementation
- `backend/app/plugins/validators/accessibility.py` - Accessibility validator implementation
- `backend/app/plugins/remediators/readability_enhancer.py` - Readability improvement plugin
- `frontend/src/features/lrd/LRDCreator.jsx` - LRD creation UI component
- `frontend/src/features/lrd/LRDCreator.test.jsx` - Tests for LRD creator
- `frontend/src/features/materials/MaterialGenerator.jsx` - Material generation UI
- `frontend/src/features/materials/MaterialGenerator.test.jsx` - Tests for material generator
- `frontend/src/features/import/ImportWizard.jsx` - Import workflow UI
- `frontend/src/features/import/ImportWizard.test.jsx` - Tests for import wizard
- `frontend/src/features/courses/CourseWizard.jsx` - Course creation wizard
- `frontend/src/features/courses/CourseWizard.test.jsx` - Tests for course wizard
- `frontend/src/components/TaskList/TaskList.jsx` - Task list management UI
- `frontend/src/components/VersionHistory/VersionHistory.jsx` - Version control UI

### Notes

- Unit tests should typically be placed alongside the code files they are testing (e.g., `course.py` and `course.test.py` in the same directory).
- Use `npx jest [optional/path/to/test/file]` to run frontend tests. Running without a path executes all tests found by the Jest configuration.
- Use `pytest [optional/path/to/test/file]` to run backend tests.

## Testing Strategy

- **Unit Tests:** Test individual components, services, and models in isolation
- **Integration Tests:** Test API endpoints and component interactions
- **End-to-End Tests:** Test complete user workflows (course creation, import, enhancement)
- **Accessibility Tests:** Verify WCAG compliance and screen reader compatibility

## Tasks (Updated: Actual Implementation Status)

- [x] 1.0 Database Schema Implementation [Effort: L] [Priority: High] ✅ COMPLETED
  - [x] 1.1 Create SQLAlchemy models for users and authentication ✅
  - [x] 1.2 Create models for courses and modules ✅
  - [x] 1.3 Create models for LRDs with version tracking ✅
  - [x] 1.4 Create models for materials with content versioning ✅
  - [x] 1.5 Create models for conversations and task lists ✅
  - [x] 1.6 Set up Alembic migrations ✅
  - [x] 1.7 Create database initialization script ✅
  - [ ] 1.8 Write unit tests for all models ❌ [Tests exist but minimal coverage]

- [x] 2.0 LRD System Implementation [Effort: L] [Priority: High] ✅ COMPLETED
  - [x] 2.1 Create LRD service with CRUD operations ✅ [507 lines implemented]
  - [x] 2.2 Implement LRD approval workflow ✅
  - [x] 2.3 Create task list generation from LRD ✅
  - [x] 2.4 Implement task tracking and status updates ✅
  - [x] 2.5 Create API endpoints for LRD management ✅
  - [x] 2.6 Add Pydantic schemas for LRD data ✅
  - [x] 2.7 Implement conversation history linking ✅
  - [ ] 2.8 Write integration tests for LRD endpoints ❌ [Tests needed]

- [x] 3.0 Content Generation System [Effort: L] [Priority: High] ✅ COMPLETED
  - [x] 3.1 Create content generator service architecture ✅ [Advanced LLM service 550 lines]
  - [x] 3.2 Implement lecture generator with teaching styles ✅
  - [x] 3.3 Implement worksheet and exercise generator ✅
  - [x] 3.4 Implement quiz and assessment generator ✅
  - [x] 3.5 Implement lab and hands-on activity generator ✅
  - [x] 3.6 Implement case study generator ✅
  - [x] 3.7 Implement interactive HTML generator ✅
  - [x] 3.8 Create content validation pipeline ✅ [Plugin system working]
  - [x] 3.9 Add streaming support for generation ✅
  - [ ] 3.10 Write unit tests for generators ❌ [Tests needed]

- [ ] 4.0 Import and Enhancement System [Effort: M] [Priority: High] ⚠️ PARTIALLY DONE
  - [x] 4.1 Create file upload and processing service ✅ [Endpoints exist]
  - [ ] 4.2 Implement content extraction from documents ❌ [Not implemented]
  - [ ] 4.3 Create content categorization system ❌ [Not implemented]
  - [ ] 4.4 Implement gap analysis for imported content ❌ [Not implemented]
  - [x] 4.5 Create enhancement pipeline with LLM ✅ [Enhancement API exists]
  - [ ] 4.6 Add batch import capability ❌ [Not implemented]
  - [ ] 4.7 Implement import validation and error handling ❌ [Basic only]
  - [ ] 4.8 Write tests for import service ❌ [Tests needed]

- [x] 5.0 Version Control System [Effort: M] [Priority: High] ✅ COMPLETED
  - [x] 5.1 Implement material versioning with parent tracking ✅
  - [x] 5.2 Create version comparison functionality ✅
  - [x] 5.3 Implement rollback mechanism ✅
  - [x] 5.4 Add branching and merging support ✅ [Clone functionality]
  - [x] 5.5 Create change tracking and justification ✅
  - [x] 5.6 Implement version history API endpoints ✅ [953 lines in materials.py]
  - [ ] 5.7 Write tests for version control ❌ [Tests needed]

- [x] 6.0 Plugin System Implementation [Effort: M] [Priority: Medium] ✅ COMPLETED
  - [x] 6.1 Implement readability validator ✅ [Spell checker with tech terms]
  - [x] 6.2 Implement structure validator ✅ [Grammar validator]
  - [x] 6.3 Implement accessibility validator ✅
  - [x] 6.4 Implement objective alignment validator ✅ [URL verifier]
  - [x] 6.5 Create readability enhancer remediator ✅
  - [x] 6.6 Create structure optimizer remediator ✅
  - [x] 6.7 Implement plugin discovery and registration ✅ [274 lines plugin manager]
  - [ ] 6.8 Write tests for validators and remediators ❌ [Tests needed]

- [ ] 7.0 Frontend UI Implementation [Effort: L] [Priority: High]
  - [ ] 7.1 Create course creation wizard component [Definition of Done: Multi-step wizard with validation]
  - [ ] 7.2 Implement LRD creator interface [Definition of Done: Form-based LRD creation]
  - [ ] 7.3 Build material generator UI with preview [Definition of Done: Split view with live preview]
  - [ ] 7.4 Create import wizard with progress tracking [Definition of Done: Drag-drop with status]
  - [ ] 7.5 Implement task list management interface [Definition of Done: Kanban-style task board]
  - [ ] 7.6 Build version history browser [Definition of Done: Visual version tree]
  - [ ] 7.7 Create course dashboard with progress indicators [Definition of Done: Cards with completion status]
  - [ ] 7.8 Implement teaching philosophy selector [Definition of Done: Quiz-based detection]
  - [ ] 7.9 Add export functionality UI [Definition of Done: Multiple format options]
  - [ ] 7.10 Write component tests [Definition of Done: All components tested]

## NEW PRIORITY TASKS (Based on Actual Gaps)

### 8.0 Critical Frontend Completion [Effort: L] [Priority: CRITICAL]
- [x] 8.1 Complete LRD Creator UI component [Connect to working backend API] ✅ COMPLETED
- [x] 8.2 Build Import Wizard with file parsing [PDF/DOCX/PPTX extraction] ✅ COMPLETED
- [x] 8.3 Create Course Dashboard with real data [Connect to materials API] ✅ COMPLETED
- [x] 8.4 Implement Task Management UI [Kanban board for LRD tasks] ✅ COMPLETED
- [ ] 8.5 Build Version History Browser [Visual diff interface]
- [ ] 8.6 Create Admin Dashboard [User management, settings]

### 9.0 File Import Processing [Effort: M] [Priority: HIGH] ✅ COMPLETED
- [x] 9.1 Implement PDF content extraction [PyPDF2 integrated] ✅
- [x] 9.2 Implement DOCX parser [python-docx integrated] ✅
- [x] 9.3 Implement PPTX slide extraction [python-pptx integrated] ✅
- [x] 9.4 Create intelligent content categorization [Pattern-based detection] ✅
- [x] 9.5 Build gap analysis engine [Comprehensive gap detection] ✅

### 10.0 Testing Infrastructure [Effort: M] [Priority: HIGH]
- [ ] 10.1 Write comprehensive backend unit tests [Target 80% coverage]
- [ ] 10.2 Create API integration test suite [Test all endpoints]
- [ ] 10.3 Build frontend component tests [React Testing Library]
- [ ] 10.4 Implement E2E test scenarios [Playwright/Cypress]
- [ ] 10.5 Set up CI/CD pipeline [GitHub Actions]

### 11.0 LLM Provider Configuration [Effort: M] [Priority: HIGH] ✅ COMPLETED
- [x] 11.1 Add system-wide LLM provider settings to database
- [x] 11.2 Implement user BYOK (Bring Your Own Key) capability
- [x] 11.3 Update backend LLM service to use provider preferences
- [x] 11.4 Add user LLM configuration UI in Settings
- [x] 11.5 Create provider status endpoint for frontend
- [ ] 11.6 Create admin UI for system-wide LLM settings

### 12.0 Production Readiness [Effort: S] [Priority: MEDIUM]
- [ ] 12.1 Add comprehensive error handling and logging
- [ ] 12.2 Implement rate limiting and API throttling
- [ ] 12.3 Set up monitoring and alerting (Sentry/DataDog)
- [ ] 12.4 Create deployment configuration (Docker/K8s)
- [ ] 12.5 Write API documentation (OpenAPI/Swagger)

### Task Legend
- **Effort:** S (Small: <4 hours), M (Medium: 4-8 hours), L (Large: >8 hours)
- **Priority:** High (blocking), Medium (important), Low (nice-to-have), CRITICAL (immediate need)
- **Definition of Done:** Specific criteria that must be met to consider the task complete
- **Prerequisites:** Other tasks that must be completed first

---

## Implementation Summary (UPDATED - December 2024)

### ACTUAL COMPLETION STATUS:
✅ **COMPLETED (Backend 90% Done)**:
1. **Database Schema** - FULLY IMPLEMENTED (22 tables, relationships, migrations)
2. **LRD System** - PRODUCTION READY (507 lines, full CRUD, approval workflow)
3. **Content Generation** - ADVANCED (550 lines, pedagogy-aware, streaming)
4. **Version Control** - COMPLETE (full versioning, rollback, history)
5. **Plugin System** - WORKING (plugin manager, 4+ validators/remediators)
6. **Authentication** - ENTERPRISE GRADE (JWT, roles, security logging)

⚠️ **PARTIALLY COMPLETE**:
- **Import System** (4.0) - Upload endpoints exist, but no file parsing
- **Frontend UI** (7.0) - Basic components only, missing key interfaces

❌ **MAJOR GAPS REQUIRING IMMEDIATE ATTENTION**:
1. **Frontend UI Components** - LRD Creator, Import Wizard, Course Dashboard
2. **File Import Processing** - PDF/DOCX/PPTX content extraction
3. **Test Coverage** - Minimal tests despite configured infrastructure
4. **Production Setup** - Docker, monitoring, documentation

### NEXT PRIORITY ACTIONS:
1. **Task 8.0** - Complete critical frontend components (CRITICAL)
2. **Task 9.0** - Implement file import processing (HIGH)
3. **Task 10.0** - Build comprehensive test suite (HIGH)
4. **Task 11.0** - Production readiness (MEDIUM)

### Revised Effort Estimate:
- Frontend completion: ~24 hours
- Import processing: ~16 hours
- Testing: ~16 hours
- Production setup: ~8 hours
- **Total to MVP: ~64 hours (8 days)**

**Current Status**: Backend essentially complete. Frontend and import processing are the critical path to MVP.

---

## NEW: Content Creation Workflow Improvements (Added 2025-08-16)

### 13.0 Course Structure Foundation [Effort: L] [Priority: HIGH]
- [ ] 13.1 Create CourseOutline model with relationships
- [ ] 13.2 Create UnitLearningOutcome model (CLO/ULO/WLO types)
- [ ] 13.3 Create WeeklyTopic model for schedule management
- [ ] 13.4 Create AssessmentPlan model for evaluation tracking
- [ ] 13.5 Update Content model with week_number and categories
- [ ] 13.6 Generate and apply database migrations

### 14.0 PDF Import & Parsing Enhancement [Effort: L] [Priority: HIGH]
- [ ] 14.1 Implement advanced PDF parsing service (PyPDF2/pdfplumber)
- [ ] 14.2 Create structure detection algorithms for outlines
- [ ] 14.3 Build mapping service for extracted data
- [ ] 14.4 Add import API endpoints for PDF outlines
- [ ] 14.5 Create frontend PDF upload component with preview

### 15.0 Guided Content Creation Workflow [Effort: XL] [Priority: HIGH]
- [ ] 15.1 Create ChatSession model for conversation history
- [ ] 15.2 Build workflow state machine (syllabus → CLOs → ULOs → weekly)
- [ ] 15.3 Implement context-aware prompting system
- [ ] 15.4 Create streaming chat interface (WebSocket/SSE)
- [ ] 15.5 Build content generation from chat decisions

### 16.0 Quality Assurance Features [Effort: L] [Priority: MEDIUM]
- [ ] 16.1 Create alignment checker service
- [ ] 16.2 Build gap analysis tool
- [ ] 16.3 Implement consistency validator
- [ ] 16.4 Create quality dashboard with visualizations
- [ ] 16.5 Add batch validation API

### Task Legend Update
- **Effort:** S (Small: <4 hours), M (Medium: 4-8 hours), L (Large: >8 hours), XL (Extra Large: >16 hours)

### Implementation Notes
- Tasks 13-16 align with docs/instructional-design-workflow.md
- Full tracking document at tasks/content-creation-workflow-improvements.md
- LRD document at docs/LRD-content-creation-system-v1.0.md