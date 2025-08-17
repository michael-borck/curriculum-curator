# Content Creation Workflow Improvements Task List

## Status: In Progress
## Created: 2025-08-16
## Aligned with: docs/instructional-design-workflow.md

## Overview
Transform the basic rich text editor into a structured curriculum development platform with conversational AI guidance, PDF import capabilities, and quality assurance features.

## Phase 1: Course Structure Foundation ⏳
**Goal:** Establish database models and relationships for structured curriculum content

### Tasks:
- [ ] **1.1 Create CourseOutline Model**
  - Fields: course_id, title, description, duration_weeks, credit_points
  - Relationships: learning_outcomes, weekly_topics, assessments
  
- [ ] **1.2 Create UnitLearningOutcome Model**  
  - Fields: unit_id, outcome_text, bloom_level, sequence_order
  - Types: CLO (Course), ULO (Unit), WLO (Weekly)
  
- [ ] **1.3 Create WeeklyTopic Model**
  - Fields: week_number, topic_title, pre_class_modules, in_class_activities
  - Relationships: learning_outcomes, content_items
  
- [ ] **1.4 Create AssessmentPlan Model**
  - Fields: assessment_type, weight_percentage, due_week, description
  - Types: formative, summative
  
- [ ] **1.5 Update Content Model**
  - Add: week_number, content_category (pre/in/post)
  - Add: learning_outcome_ids (many-to-many)
  
- [ ] **1.6 Create database migrations**
  - Run alembic to generate and apply migrations

### Files to Create/Modify:
- `backend/app/models/course_outline.py`
- `backend/app/models/learning_outcome.py`
- `backend/app/models/weekly_topic.py`
- `backend/app/models/assessment_plan.py`
- `backend/app/models/content.py` (update)
- `backend/app/schemas/course_structure.py`

## Phase 2: PDF Import & Parsing 📄
**Goal:** Enable extraction of unit outlines and existing materials from PDFs

### Tasks:
- [ ] **2.1 Implement PDF parsing service**
  - Use PyPDF2/pdfplumber for text extraction
  - Pattern recognition for sections (objectives, topics, assessments)
  
- [ ] **2.2 Create structure detection algorithms**
  - Identify learning outcomes patterns
  - Extract weekly schedule
  - Parse assessment information
  
- [ ] **2.3 Build mapping service**
  - Map extracted data to database models
  - Handle ambiguous content with user confirmation
  
- [ ] **2.4 Create import API endpoints**
  - POST /api/import/pdf-outline
  - GET /api/import/status/{import_id}
  
- [ ] **2.5 Add frontend PDF upload component**
  - Drag-drop interface
  - Preview extracted structure
  - Manual correction interface

### Files to Create/Modify:
- `backend/app/services/pdf_parser.py`
- `backend/app/services/structure_detector.py`
- `backend/app/api/routes/import.py`
- `frontend/src/features/import/PDFOutlineImport.tsx`

## Phase 3: Guided Content Creation Workflow 🤖
**Goal:** Implement conversational AI interface for curriculum development

### Tasks:
- [ ] **3.1 Create ChatSession Model**
  - Store conversation history
  - Track workflow stage
  - Link to generated content
  
- [ ] **3.2 Build workflow state machine**
  - States: syllabus → CLOs → ULOs → weekly_plan → content
  - Transitions with validation
  
- [ ] **3.3 Implement context-aware prompting**
  - Stage-specific question templates
  - Maintain conversation context
  - Generate clarifying questions
  
- [ ] **3.4 Create streaming chat interface**
  - WebSocket or SSE for real-time responses
  - Show workflow progress
  - Allow backtracking
  
- [ ] **3.5 Build content generation from chat**
  - Convert chat decisions to structured content
  - Apply selected pedagogy throughout
  - Generate aligned materials

### Files to Create/Modify:
- `backend/app/models/chat_session.py`
- `backend/app/services/workflow_engine.py`
- `backend/app/services/chat_llm_service.py`
- `backend/app/api/routes/chat_workflow.py`
- `frontend/src/features/chat/WorkflowChat.tsx`
- `frontend/src/features/chat/WorkflowProgress.tsx`

## Phase 4: Quality Assurance Features ✅
**Goal:** Ensure content quality and alignment with learning objectives

### Tasks:
- [ ] **4.1 Create alignment checker service**
  - Verify content maps to learning outcomes
  - Check Bloom's taxonomy coverage
  - Validate assessment alignment
  
- [ ] **4.2 Build gap analysis tool**
  - Identify missing topics
  - Suggest additional content
  - Flag over/under-represented areas
  
- [ ] **4.3 Implement consistency validator**
  - Check terminology consistency
  - Verify difficulty progression
  - Validate time allocations
  
- [ ] **4.4 Create quality dashboard**
  - Visual alignment matrix
  - Coverage heat maps
  - Improvement suggestions
  
- [ ] **4.5 Add batch validation API**
  - Validate entire course structure
  - Generate quality reports
  - Export compliance documentation

### Files to Create/Modify:
- `backend/app/services/quality_checker.py`
- `backend/app/services/gap_analyzer.py`
- `backend/app/api/routes/quality.py`
- `frontend/src/features/quality/QualityDashboard.tsx`
- `frontend/src/features/quality/AlignmentMatrix.tsx`

## Integration Points 🔗

### With Existing Features:
- **LLM Service:** Enhance with workflow-aware prompting
- **Content Model:** Extend for structured curriculum
- **Import System:** Add PDF parsing capabilities
- **Export System:** Include LRD generation

### New API Endpoints:
```
POST   /api/courses/{id}/outline          - Create course outline
GET    /api/courses/{id}/structure        - Get full structure
POST   /api/chat/workflow/start           - Start guided creation
POST   /api/chat/workflow/message         - Send chat message
GET    /api/chat/workflow/status          - Get workflow status
POST   /api/import/pdf-outline            - Import PDF outline
GET    /api/quality/alignment/{course_id} - Check alignment
GET    /api/quality/gaps/{course_id}      - Analyze gaps
```

## Success Metrics 📊
- [ ] Course creation time reduced by 50%
- [ ] 100% learning outcome alignment
- [ ] PDF import success rate > 80%
- [ ] User satisfaction score > 4.5/5
- [ ] Quality check pass rate > 90%

## Testing Strategy 🧪
- Unit tests for parser and validators
- Integration tests for workflow engine
- E2E tests for complete creation flow
- User acceptance testing with educators

## Rollback Plan 🔄
- Feature flags for each phase
- Database migrations reversible
- Keep original editor as fallback
- Gradual rollout to users

## Dependencies 📦
- PyPDF2 or pdfplumber for PDF parsing
- Extended LangChain for workflow management
- Additional frontend: workflow visualization library
- Database: PostgreSQL recommended for JSON fields

## Notes
- Aligned with flipped classroom pedagogy from instructional-design-workflow.md
- Supports Australian university terminology and structure
- Maintains backward compatibility with existing content

## Completion Checklist
- [ ] All models created and migrated
- [ ] PDF import tested with 10+ real outlines
- [ ] Workflow handles all edge cases
- [ ] Quality checks comprehensive
- [ ] Documentation updated
- [ ] User training materials created