# Unit Structure & Assessment Management Implementation Plan

## Executive Summary
Implementation of a comprehensive unit structure and assessment management system for the Curriculum Curator platform, enabling educators to create, organize, and manage course content with hierarchical learning outcomes, weekly materials, and assessments.

## Architecture Overview

### Database Schema Design

#### Core Tables

1. **unit_learning_outcomes** (ULOs)
   - id: UUID (primary key)
   - unit_id: UUID (foreign key → units)
   - code: String (e.g., "ULO1", "ULO2")
   - description: Text
   - bloom_level: Enum (remember, understand, apply, analyze, evaluate, create)
   - order_index: Integer
   - created_at, updated_at: Timestamp

2. **weekly_materials** (Content Items)
   - id: UUID (primary key)
   - unit_id: UUID (foreign key → units)
   - week_number: Integer
   - title: String
   - type: Enum (lecture, handout, quiz, case_study, resource, notes)
   - description: Text
   - duration_minutes: Integer (optional)
   - file_path: String (for git-stored content)
   - metadata: JSON (pages, questions, etc.)
   - order_index: Integer
   - status: Enum (draft, complete, needs_review)
   - created_at, updated_at: Timestamp

3. **local_learning_outcomes** (LLOs - Material-specific)
   - id: UUID (primary key)
   - material_id: UUID (foreign key → weekly_materials)
   - description: Text
   - order_index: Integer

4. **weekly_learning_outcomes** (WLOs)
   - id: UUID (primary key)
   - unit_id: UUID (foreign key → units)
   - week_number: Integer
   - description: Text
   - order_index: Integer

5. **assessments**
   - id: UUID (primary key)
   - unit_id: UUID (foreign key → units)
   - title: String
   - type: Enum (formative, summative)
   - category: Enum (quiz, exam, project, discussion, paper, presentation)
   - weight: Float (0-100)
   - description: Text
   - specification: Text (detailed requirements)
   - release_week: Integer
   - release_date: Date
   - due_week: Integer
   - due_date: Date
   - duration: String (optional)
   - rubric: JSON (optional)
   - status: Enum (draft, complete, needs_review)
   - created_at, updated_at: Timestamp

6. **assessment_learning_outcomes** (ALOs)
   - id: UUID (primary key)
   - assessment_id: UUID (foreign key → assessments)
   - description: Text
   - order_index: Integer

#### Mapping Tables (Many-to-Many)

7. **material_ulo_mappings**
   - material_id: UUID (foreign key → weekly_materials)
   - ulo_id: UUID (foreign key → unit_learning_outcomes)
   - Primary key: (material_id, ulo_id)

8. **assessment_ulo_mappings**
   - assessment_id: UUID (foreign key → assessments)
   - ulo_id: UUID (foreign key → unit_learning_outcomes)
   - Primary key: (assessment_id, ulo_id)

9. **wlo_ulo_mappings** (Optional)
   - wlo_id: UUID (foreign key → weekly_learning_outcomes)
   - ulo_id: UUID (foreign key → unit_learning_outcomes)
   - Primary key: (wlo_id, ulo_id)

10. **assessment_material_links**
    - assessment_id: UUID (foreign key → assessments)
    - material_id: UUID (foreign key → weekly_materials)
    - Primary key: (assessment_id, material_id)

### API Endpoints Structure

#### Unit Learning Outcomes
- `GET /api/units/{unit_id}/learning-outcomes` - List all ULOs
- `POST /api/units/{unit_id}/learning-outcomes` - Create ULO
- `PUT /api/units/{unit_id}/learning-outcomes/{ulo_id}` - Update ULO
- `DELETE /api/units/{unit_id}/learning-outcomes/{ulo_id}` - Delete ULO
- `POST /api/units/{unit_id}/learning-outcomes/reorder` - Reorder ULOs

#### Weekly Materials
- `GET /api/units/{unit_id}/materials` - List all materials (with filters)
- `GET /api/units/{unit_id}/weeks/{week}/materials` - Get materials for specific week
- `POST /api/units/{unit_id}/materials` - Create material
- `PUT /api/materials/{material_id}` - Update material
- `DELETE /api/materials/{material_id}` - Delete material
- `POST /api/materials/{material_id}/duplicate` - Duplicate material
- `POST /api/materials/{material_id}/mappings` - Update ULO mappings

#### Assessments
- `GET /api/units/{unit_id}/assessments` - List all assessments
- `POST /api/units/{unit_id}/assessments` - Create assessment
- `PUT /api/assessments/{assessment_id}` - Update assessment
- `DELETE /api/assessments/{assessment_id}` - Delete assessment
- `GET /api/units/{unit_id}/assessments/grade-distribution` - Get grade weight summary
- `POST /api/assessments/{assessment_id}/mappings` - Update ULO mappings

#### Analytics & Coverage
- `GET /api/units/{unit_id}/outcome-coverage` - Analyze ULO coverage
- `GET /api/units/{unit_id}/assessment-timeline` - Get assessment schedule
- `GET /api/units/{unit_id}/workload-analysis` - Analyze weekly workload

### Frontend Components Architecture

#### Pages
1. **UnitStructurePage** - Main dashboard with tabs
2. **WeeklyMaterialsView** - Weekly content management
3. **AssessmentsView** - Assessment management
4. **GradeDistributionView** - Grade weight visualization

#### Components

##### Core Components
- `UnitStructureDashboard` - Main container with tab navigation
- `ULOManager` - CRUD for Unit Learning Outcomes
- `WeekManager` - Weekly content organization
- `MaterialCard` - Individual material display/edit
- `AssessmentCard` - Individual assessment display/edit
- `OutcomeMappingModal` - Map materials/assessments to ULOs
- `GradeDistributionChart` - Visual grade weight display

##### Supporting Components
- `MaterialTypeSelector` - Icon-based type selection
- `DifficultyBadge` - Visual difficulty indicator
- `StatusBadge` - Completion status indicator
- `DateRangePicker` - Week/calendar date selector
- `RubricBuilder` - Assessment rubric creation
- `BulkActionBar` - Multi-select operations
- `ImportModal` - PDF/file import interface

## Implementation Phases

### Phase 1: Database & API Foundation (Week 1)
1. Create all database migrations
2. Implement SQLAlchemy models
3. Create Pydantic schemas
4. Build CRUD services
5. Implement basic API endpoints
6. Write unit tests for models and services

### Phase 2: Core Frontend Structure (Week 1-2)
1. Create main dashboard layout with tabs
2. Implement ULO management interface
3. Build weekly materials view
4. Create material cards with basic CRUD
5. Implement drag-and-drop reordering
6. Add filtering and search functionality

### Phase 3: Assessment Management (Week 2)
1. Create assessment management view
2. Implement assessment CRUD operations
3. Build grade distribution calculator
4. Add timeline visualization
5. Create rubric builder interface
6. Implement validation for 100% weight

### Phase 4: Learning Outcome Mapping (Week 3)
1. Build outcome mapping interface
2. Create coverage analysis view
3. Implement gap identification
4. Add visual mapping indicators
5. Create alignment matrix export

### Phase 5: Content Storage & Versioning (Week 3)
1. Implement git-based content storage
2. Create markdown file structure
3. Build version history viewer
4. Add diff visualization
5. Implement rollback functionality

### Phase 6: AI Integration (Week 4)
1. Create AI content generation endpoints
2. Build suggestion interface
3. Implement enhancement features
4. Add outcome generation
5. Create question generation from content

### Phase 7: Import/Export & Templates (Week 4)
1. Build PDF import processor
2. Create LMS export formats
3. Implement template system
4. Add bulk import interface
5. Create course cloning

### Phase 8: Polish & Optimization (Week 5)
1. Performance optimization
2. Accessibility improvements
3. Mobile responsiveness
4. Error handling enhancement
5. User testing & feedback incorporation

## Technical Specifications

### State Management
- Use Zustand for global state (unit data, assessments)
- React Query for server state and caching
- Local state for UI-only concerns

### Data Flow
1. User actions trigger API calls
2. Optimistic updates for better UX
3. Background sync for git storage
4. Real-time validation feedback

### Performance Considerations
- Lazy load week contents
- Virtual scrolling for long lists
- Debounced search/filter
- Cached API responses
- Progressive content loading

### Error Handling
- Form validation with clear messages
- API error recovery strategies
- Unsaved changes warnings
- Conflict resolution for concurrent edits

## Testing Strategy

### Backend Testing
- Unit tests for all models and services
- Integration tests for API endpoints
- Load testing for performance
- Security testing for access control

### Frontend Testing
- Component unit tests with React Testing Library
- Integration tests for user flows
- E2E tests for critical paths
- Visual regression testing

## Migration from Current System

### Data Migration
1. Preserve existing unit data
2. Generate default ULOs from existing content
3. Convert existing materials to new structure
4. Maintain user permissions

### Backward Compatibility
- Keep existing endpoints operational
- Gradual feature rollout
- Feature flags for new functionality
- Parallel run period

## Success Metrics

### Quantitative
- 100% of units have defined ULOs
- All assessments mapped to outcomes
- Grade weights sum to 100%
- < 2s page load time
- < 100ms interaction response

### Qualitative
- Improved content organization
- Clear learning outcome alignment
- Streamlined assessment planning
- Enhanced collaboration features
- Positive user feedback

## Risk Mitigation

### Technical Risks
- **Database complexity**: Use proper indexing and query optimization
- **Frontend performance**: Implement code splitting and lazy loading
- **Data loss**: Regular backups and git versioning
- **Integration issues**: Comprehensive testing and staging environment

### User Adoption Risks
- **Learning curve**: Provide tutorials and documentation
- **Migration concerns**: Offer import tools and support
- **Feature overload**: Progressive disclosure and sensible defaults

## Dependencies

### External Services
- Git for content versioning
- LLM APIs for AI features
- File storage for uploads
- Email service for notifications

### Internal Dependencies
- Authentication system
- User management
- File upload service
- LLM integration service

## Timeline Summary

- **Week 1**: Database, models, basic API
- **Week 2**: Core frontend, materials, assessments
- **Week 3**: Mappings, versioning
- **Week 4**: AI integration, import/export
- **Week 5**: Polish, testing, deployment

Total estimated time: 5 weeks for full implementation

## Next Steps

1. Review and approve implementation plan
2. Finalize database schema
3. Set up development branch
4. Begin Phase 1 implementation
5. Schedule regular progress reviews