# Unit Structure & Assessment Management - Implementation Tasks

## Overview
Detailed task breakdown for implementing the unit structure and assessment management system as specified in the implementation plan.

---

## Phase 1: Database & API Foundation

### Parent Task 1: Database Schema Implementation
**Priority**: Critical  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 1.1 Create database migration for unit_learning_outcomes table
  - File: `backend/alembic/versions/xxx_add_unit_learning_outcomes.py`
  - Fields: id, unit_id, code, description, bloom_level, order_index, timestamps

- [ ] 1.2 Create database migration for weekly_materials table
  - File: `backend/alembic/versions/xxx_add_weekly_materials.py`
  - Fields: id, unit_id, week_number, title, type, description, duration_minutes, file_path, metadata, order_index, status, timestamps

- [ ] 1.3 Create database migration for assessments table
  - File: `backend/alembic/versions/xxx_add_assessments.py`
  - Fields: id, unit_id, title, type, category, weight, description, specification, release/due dates, duration, rubric, status, timestamps

- [ ] 1.4 Create database migration for learning outcome tables
  - File: `backend/alembic/versions/xxx_add_learning_outcomes.py`
  - Tables: local_learning_outcomes, weekly_learning_outcomes, assessment_learning_outcomes

- [ ] 1.5 Create database migration for mapping tables
  - File: `backend/alembic/versions/xxx_add_mapping_tables.py`
  - Tables: material_ulo_mappings, assessment_ulo_mappings, wlo_ulo_mappings, assessment_material_links

- [ ] 1.6 Run and test all migrations
  - Command: `alembic upgrade head`
  - Verify all tables and relationships

### Parent Task 2: SQLAlchemy Models
**Priority**: Critical  
**Estimated Time**: 1 day

#### Sub-tasks:
- [ ] 2.1 Create UnitLearningOutcome model
  - File: `backend/app/models/unit_learning_outcome.py`
  - Include relationships to materials and assessments

- [ ] 2.2 Create WeeklyMaterial model
  - File: `backend/app/models/weekly_material.py`
  - Include relationships to outcomes and unit

- [ ] 2.3 Create Assessment model
  - File: `backend/app/models/assessment.py`
  - Include relationships to outcomes and materials

- [ ] 2.4 Create supporting outcome models
  - File: `backend/app/models/learning_outcomes.py`
  - Models: LocalLearningOutcome, WeeklyLearningOutcome, AssessmentLearningOutcome

- [ ] 2.5 Update Unit model with new relationships
  - File: `backend/app/models/unit.py`
  - Add relationships to learning_outcomes, materials, assessments

### Parent Task 3: Pydantic Schemas
**Priority**: High  
**Estimated Time**: 1 day

#### Sub-tasks:
- [ ] 3.1 Create learning outcome schemas
  - File: `backend/app/schemas/learning_outcomes.py`
  - Schemas: ULOCreate, ULOUpdate, ULOResponse, etc.

- [ ] 3.2 Create material schemas
  - File: `backend/app/schemas/materials.py`
  - Schemas: MaterialCreate, MaterialUpdate, MaterialResponse, MaterialWithOutcomes

- [ ] 3.3 Create assessment schemas
  - File: `backend/app/schemas/assessments.py`
  - Schemas: AssessmentCreate, AssessmentUpdate, AssessmentResponse, GradeDistribution

- [ ] 3.4 Create mapping schemas
  - File: `backend/app/schemas/mappings.py`
  - Schemas: OutcomeMapping, MaterialMapping, AssessmentMapping

### Parent Task 4: CRUD Services
**Priority**: High  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 4.1 Create ULO service
  - File: `backend/app/services/ulo_service.py`
  - Methods: create, update, delete, reorder, get_by_unit

- [ ] 4.2 Create materials service
  - File: `backend/app/services/materials_service.py`
  - Methods: create, update, delete, duplicate, get_by_week, update_mappings

- [ ] 4.3 Create assessments service
  - File: `backend/app/services/assessments_service.py`
  - Methods: create, update, delete, calculate_distribution, validate_weights

- [ ] 4.4 Create analytics service
  - File: `backend/app/services/analytics_service.py`
  - Methods: analyze_coverage, calculate_workload, identify_gaps

### Parent Task 5: API Endpoints
**Priority**: High  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 5.1 Create learning outcomes endpoints
  - File: `backend/app/api/routes/learning_outcomes.py`
  - Endpoints: CRUD operations, reordering, bulk operations

- [ ] 5.2 Create materials endpoints
  - File: `backend/app/api/routes/materials.py`
  - Endpoints: CRUD, filtering, duplication, mapping

- [ ] 5.3 Create assessments endpoints
  - File: `backend/app/api/routes/assessments.py`
  - Endpoints: CRUD, grade distribution, timeline

- [ ] 5.4 Create analytics endpoints
  - File: `backend/app/api/routes/analytics.py`
  - Endpoints: coverage, workload, alignment matrix

- [ ] 5.5 Register all new routes
  - File: `backend/app/main.py`
  - Include all new routers

---

## Phase 2: Core Frontend Structure

### Parent Task 6: Dashboard Layout
**Priority**: Critical  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 6.1 Create UnitStructurePage component
  - File: `frontend/src/pages/UnitStructurePage.tsx`
  - Layout with tabs, header, sidebar

- [ ] 6.2 Create tab navigation component
  - File: `frontend/src/components/UnitStructure/TabNavigation.tsx`
  - Tabs: Weekly Materials, Assessments, Grade Distribution

- [ ] 6.3 Create sidebar component
  - File: `frontend/src/components/UnitStructure/Sidebar.tsx`
  - Week list, filters, search

- [ ] 6.4 Update routing
  - File: `frontend/src/App.tsx`
  - Add route for unit structure page

### Parent Task 7: ULO Management
**Priority**: High  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 7.1 Create ULOManager component
  - File: `frontend/src/components/UnitStructure/ULOManager.tsx`
  - CRUD interface for ULOs

- [ ] 7.2 Create ULOCard component
  - File: `frontend/src/components/UnitStructure/ULOCard.tsx`
  - Display and edit individual ULO

- [ ] 7.3 Create ULO API service
  - File: `frontend/src/services/uloApi.ts`
  - API calls for ULO operations

- [ ] 7.4 Create ULO store
  - File: `frontend/src/stores/uloStore.ts`
  - Zustand store for ULO state

### Parent Task 8: Weekly Materials View
**Priority**: High  
**Estimated Time**: 3 days

#### Sub-tasks:
- [ ] 8.1 Create WeeklyMaterialsView component
  - File: `frontend/src/components/UnitStructure/WeeklyMaterialsView.tsx`
  - Main materials management interface

- [ ] 8.2 Create MaterialCard component
  - File: `frontend/src/components/UnitStructure/MaterialCard.tsx`
  - Display individual material with actions

- [ ] 8.3 Create MaterialEditModal component
  - File: `frontend/src/components/UnitStructure/MaterialEditModal.tsx`
  - Form for creating/editing materials

- [ ] 8.4 Create MaterialTypeSelector component
  - File: `frontend/src/components/UnitStructure/MaterialTypeSelector.tsx`
  - Icon-based type selection

- [ ] 8.5 Create materials API service
  - File: `frontend/src/services/materialsApi.ts`
  - API calls for material operations

- [ ] 8.6 Implement drag-and-drop reordering
  - File: `frontend/src/components/UnitStructure/DraggableList.tsx`
  - Reusable draggable list component

---

## Phase 3: Assessment Management

### Parent Task 9: Assessment View
**Priority**: High  
**Estimated Time**: 3 days

#### Sub-tasks:
- [ ] 9.1 Create AssessmentsView component
  - File: `frontend/src/components/UnitStructure/AssessmentsView.tsx`
  - Main assessment management interface

- [ ] 9.2 Create AssessmentCard component
  - File: `frontend/src/components/UnitStructure/AssessmentCard.tsx`
  - Display individual assessment

- [ ] 9.3 Create AssessmentEditModal component
  - File: `frontend/src/components/UnitStructure/AssessmentEditModal.tsx`
  - Form for creating/editing assessments

- [ ] 9.4 Create GradeDistributionView component
  - File: `frontend/src/components/UnitStructure/GradeDistributionView.tsx`
  - Visual grade weight display

- [ ] 9.5 Create assessments API service
  - File: `frontend/src/services/assessmentsApi.ts`
  - API calls for assessment operations

### Parent Task 10: Rubric Builder
**Priority**: Medium  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 10.1 Create RubricBuilder component
  - File: `frontend/src/components/UnitStructure/RubricBuilder.tsx`
  - Interface for creating rubrics

- [ ] 10.2 Create RubricCriterion component
  - File: `frontend/src/components/UnitStructure/RubricCriterion.tsx`
  - Individual rubric criterion editor

- [ ] 10.3 Create rubric types and utilities
  - File: `frontend/src/types/rubric.ts`
  - TypeScript types for rubrics

---

## Phase 4: Learning Outcome Mapping

### Parent Task 11: Mapping Interface
**Priority**: High  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 11.1 Create OutcomeMappingModal component
  - File: `frontend/src/components/UnitStructure/OutcomeMappingModal.tsx`
  - Interface for mapping materials/assessments to ULOs

- [ ] 11.2 Create CoverageAnalysis component
  - File: `frontend/src/components/UnitStructure/CoverageAnalysis.tsx`
  - Visual display of outcome coverage

- [ ] 11.3 Create AlignmentMatrix component
  - File: `frontend/src/components/UnitStructure/AlignmentMatrix.tsx`
  - Matrix view of outcome alignment

- [ ] 11.4 Create mapping API service
  - File: `frontend/src/services/mappingApi.ts`
  - API calls for mapping operations

---

## Phase 5: Content Storage & Versioning

### Parent Task 12: Git Integration
**Priority**: Medium  
**Estimated Time**: 3 days

#### Sub-tasks:
- [ ] 12.1 Create git service for content
  - File: `backend/app/services/git_service.py`
  - Methods: init_repo, commit_content, get_history, rollback

- [ ] 12.2 Create content storage service
  - File: `backend/app/services/content_storage_service.py`
  - Methods: save_material, load_material, get_versions

- [ ] 12.3 Create version history component
  - File: `frontend/src/components/UnitStructure/VersionHistory.tsx`
  - Display content version history

- [ ] 12.4 Create diff viewer component
  - File: `frontend/src/components/UnitStructure/DiffViewer.tsx`
  - Show changes between versions

---

## Phase 6: AI Integration

### Parent Task 13: AI Content Generation
**Priority**: Medium  
**Estimated Time**: 3 days

#### Sub-tasks:
- [ ] 13.1 Extend LLM service for content generation
  - File: `backend/app/services/llm_service.py`
  - Methods: generate_material, generate_assessment, generate_outcomes

- [ ] 13.2 Create AI suggestion endpoints
  - File: `backend/app/api/routes/ai_content.py`
  - Endpoints: generate, enhance, suggest

- [ ] 13.3 Create AI assistant component
  - File: `frontend/src/components/UnitStructure/AIAssistant.tsx`
  - Interface for AI suggestions

- [ ] 13.4 Create content enhancement modal
  - File: `frontend/src/components/UnitStructure/EnhanceModal.tsx`
  - AI-powered content improvement

---

## Phase 7: Import/Export & Templates

### Parent Task 14: Import/Export System
**Priority**: Low  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 14.1 Create export service
  - File: `backend/app/services/export_service.py`
  - Methods: export_to_canvas, export_to_moodle, export_to_scorm

- [ ] 14.2 Create import service enhancements
  - File: `backend/app/services/import_service.py`
  - Methods: import_from_pdf, import_from_docx

- [ ] 14.3 Create template service
  - File: `backend/app/services/template_service.py`
  - Methods: save_as_template, apply_template

- [ ] 14.4 Create import/export UI
  - File: `frontend/src/components/UnitStructure/ImportExportModal.tsx`
  - Interface for import/export operations

---

## Phase 8: Testing & Documentation

### Parent Task 15: Backend Testing
**Priority**: High  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 15.1 Write model tests
  - File: `backend/tests/test_models/`
  - Test all new models and relationships

- [ ] 15.2 Write service tests
  - File: `backend/tests/test_services/`
  - Test all service methods

- [ ] 15.3 Write API endpoint tests
  - File: `backend/tests/test_api/`
  - Test all new endpoints

- [ ] 15.4 Write integration tests
  - File: `backend/tests/test_integration/`
  - Test complete workflows

### Parent Task 16: Frontend Testing
**Priority**: High  
**Estimated Time**: 2 days

#### Sub-tasks:
- [ ] 16.1 Write component tests
  - Files: `frontend/src/components/**/*.test.tsx`
  - Test all new components

- [ ] 16.2 Write service tests
  - Files: `frontend/src/services/**/*.test.ts`
  - Test API services

- [ ] 16.3 Write E2E tests
  - Files: `frontend/e2e/`
  - Test critical user flows

---

## Testing Strategy

### Backend Tests Required:
- Unit tests for all models
- Service layer tests with mocked dependencies
- API endpoint tests with test database
- Integration tests for complete workflows
- Performance tests for large datasets

### Frontend Tests Required:
- Component unit tests
- Service layer tests
- Store tests
- Integration tests
- E2E tests for critical paths

---

## Files to Create/Modify Summary

### New Backend Files (25):
- Models: 5 files
- Schemas: 4 files
- Services: 8 files
- API Routes: 5 files
- Tests: 3+ directories

### New Frontend Files (35+):
- Pages: 1 file
- Components: 25+ files
- Services: 5 files
- Stores: 2 files
- Types: 3 files
- Tests: Multiple files

### Modified Files:
- `backend/app/models/unit.py`
- `backend/app/main.py`
- `frontend/src/App.tsx`
- `frontend/src/types/index.ts`

---

## Rollback Plan

If issues arise during implementation:

1. **Database Rollback**:
   - Use Alembic downgrade: `alembic downgrade -1`
   - Restore from backup if needed

2. **Code Rollback**:
   - Git revert to previous commit
   - Feature flags to disable new functionality

3. **Partial Rollback**:
   - Keep working features
   - Disable problematic components
   - Fix and redeploy

---

## Definition of Done

Each task is considered complete when:
- [ ] Code is implemented and working
- [ ] Unit tests are written and passing
- [ ] API documentation is updated
- [ ] Code passes linting (0 errors)
- [ ] TypeScript has no type errors
- [ ] Feature is tested manually
- [ ] Code is reviewed (if applicable)

---

## Next Steps

1. **Review and approve this task list**
2. **Prioritize tasks for first sprint**
3. **Set up development branch**
4. **Begin Phase 1 implementation**
5. **Daily progress updates**

---

*This task list will be updated as tasks are completed. Each task will be marked with [x] when done.*