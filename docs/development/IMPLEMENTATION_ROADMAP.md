# Curriculum Curator Implementation Roadmap

## Overview

This document outlines the implementation plan for transforming Curriculum Curator into a comprehensive course material creation and curation platform for lecturers. The system will support multiple teaching styles, course management, and both wizard-guided and power-user workflows.

## Architecture Decisions

### 1. Database vs Filesystem

**Recommendation: Hybrid Approach**
- **SQLite Database** for:
  - User authentication and profiles
  - Course metadata and structure
  - Session management and workflow state
  - Content references and relationships
  
- **Filesystem** for:
  - Generated content files (organized by user/course)
  - Uploaded materials
  - Templates and exports
  
**Structure:**
```
data/
├── users/
│   └── {user_id}/
│       ├── courses/
│       │   └── {course_id}/
│       │       ├── uploads/
│       │       ├── generated/
│       │       └── exports/
│       └── profile.json
└── shared/
    ├── templates/
    └── resources/
```

### 2. Authentication & Multi-tenancy

**Implementation:**
- FastHTML session-based authentication
- User isolation at filesystem and database level
- Role-based access (Lecturer, Admin, Assistant)

## Phase 1: Foundation & Authentication (2 weeks)

### 1.1 User Management System
```python
# core/auth.py
class AuthManager:
    - User registration/login
    - Session management
    - Password reset
    - Profile management
```

### 1.2 Database Schema
```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    name TEXT,
    institution TEXT,
    teaching_philosophy TEXT,
    created_at TIMESTAMP
);

-- Courses table
CREATE TABLE courses (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT,
    code TEXT,
    semester TEXT,
    status TEXT, -- draft, active, complete
    syllabus_data JSON,
    schedule_data JSON,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Course materials table
CREATE TABLE materials (
    id TEXT PRIMARY KEY,
    course_id TEXT,
    week_number INTEGER,
    type TEXT, -- lecture, worksheet, lab, quiz, etc.
    title TEXT,
    content JSON,
    metadata JSON,
    created_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Workflow sessions table
CREATE TABLE workflow_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT,
    workflow_type TEXT,
    state JSON,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

### 1.3 Landing Page & Dashboard
```python
# components/landing.py
- Welcome page with login/register
- Feature highlights
- Quick start guide

# components/dashboard.py
- Course grid/list view
- Quick actions (New Course, Import, Continue Working)
- Recent activity feed
- Course completion status indicators
```

## Phase 2: Course Creation Workflow (3 weeks)

### 2.1 Course Setup Wizard
```python
# workflows/course_setup.py
class CourseSetupWizard:
    steps = [
        "BasicInfo",        # Title, code, semester
        "Philosophy",       # Teaching style selection
        "Structure",        # Duration, schedule type
        "Objectives",       # Learning outcomes
        "Assessment",       # Grading structure
        "Resources"         # Textbooks, references
    ]
```

### 2.2 Syllabus Generation
```python
# core/syllabus_generator.py
class SyllabusGenerator:
    - Template selection (or upload)
    - AI-powered generation from inputs
    - Import from URL
    - Preview and edit
    - Export formats (PDF, DOCX, HTML)
```

### 2.3 Weekly Schedule Builder
```python
# components/schedule_builder.py
- Visual calendar interface
- Drag-drop topic arrangement
- Auto-distribution of topics
- Holiday/break management
- Progressive unlocking (complete week 1 before week 2)
```

## Phase 3: Content Generation System (4 weeks)

### 3.1 LLM Integration Layer
```python
# core/llm_orchestrator.py
class LLMOrchestrator:
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'gemini': GeminiProvider(),
            'ollama': OllamaProvider()
        }
    
    async def generate_content(self, request: ContentRequest):
        # Dynamic prompt building
        prompt = self.build_prompt(
            content_type=request.type,
            teaching_style=request.user.teaching_philosophy,
            context=request.context,
            preferences=request.preferences
        )
        
        # Provider selection and generation
        response = await self.selected_provider.generate(prompt)
        
        # Post-processing and validation
        return self.process_response(response)
```

### 3.2 Content Type Generators
```python
# generators/
├── lecture_generator.py
├── worksheet_generator.py
├── lab_generator.py
├── quiz_generator.py
├── case_study_generator.py
├── interactive_html_generator.py
└── scenario_generator.py

# Each generator implements:
class BaseContentGenerator:
    async def plan(self, context) -> ContentPlan
    async def generate(self, plan) -> GeneratedContent
    async def enhance(self, content) -> EnhancedContent
    async def validate(self, content) -> ValidationResult
```

### 3.3 Guided Creation Workflow
```python
# workflows/guided_creation.py
class GuidedCreationWorkflow:
    stages = [
        "PlanGeneration",      # Create outline/plan
        "PlanReview",          # User reviews and modifies
        "TodoMapping",         # Convert to actionable tasks
        "StepByStep",          # Work through each task
        "Review",              # Final review
        "Export"               # Save/export options
    ]
    
    async def execute_stage(self, stage, context):
        # Each stage requires user confirmation
        # State saved between stages
        # Can pause and resume
```

## Phase 4: Material Management & Enhancement (3 weeks)

### 4.1 Smart Upload System
```python
# core/smart_upload.py
class SmartUploadProcessor:
    - Document type detection
    - Content extraction and parsing
    - Automatic tagging and categorization
    - Learning objective extraction
    - Integration with existing materials
```

### 4.2 Reference Integration
```python
# core/reference_manager.py
class ReferenceManager:
    - URL content fetching and parsing
    - Reading list management
    - Citation generation
    - Content linking and cross-referencing
```

### 4.3 Material Enhancement Pipeline
```python
# pipelines/enhancement.py
class EnhancementPipeline:
    validators = [
        ReadabilityValidator(),
        StructureValidator(),
        ObjectiveAlignmentValidator(),
        AccessibilityValidator()
    ]
    
    remediators = [
        ContentEnhancer(),
        ExampleGenerator(),
        InteractivityAdder(),
        VisualizationSuggester()
    ]
```

## Phase 5: User Interface Implementation (3 weeks)

### 5.1 Wizard Mode (Beginners)
```python
# ui/wizard_mode.py
Features:
- Step-by-step guidance
- Contextual help and examples
- Pre-filled templates
- Validation at each step
- Progress saving
- Undo/redo functionality
```

### 5.2 Expert Mode (Power Users)
```python
# ui/expert_mode.py
Features:
- Command palette (Ctrl+K)
- Bulk operations
- Direct prompt editing
- Keyboard shortcuts
- Multiple panels/tabs
- Advanced search and filters
```

### 5.3 Common UI Components
```python
# components/common/
├── material_card.py      # Display material with actions
├── preview_panel.py      # Live preview of content
├── property_editor.py    # Edit material properties
├── version_history.py    # Track changes
├── export_dialog.py      # Export options
└── settings_panel.py     # User preferences
```

## Phase 6: Advanced Features (4 weeks)

### 6.1 Interactive Content Creation
```python
# features/interactive_content.py
- HTML5 interactive exercises
- Self-grading components
- Embedded simulations
- Code playgrounds
- Video annotations
```

### 6.2 Collaboration Features
```python
# features/collaboration.py
- Share courses (read-only)
- Co-instructor management
- Comment system
- Change suggestions
- Version control
```

### 6.3 Analytics & Insights
```python
# features/analytics.py
- Content coverage analysis
- Learning objective mapping
- Time estimation
- Difficulty progression
- Student engagement predictions
```

## Implementation Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | Auth system, Database, Dashboard |
| Phase 2 | 3 weeks | Course wizard, Syllabus, Schedule |
| Phase 3 | 4 weeks | LLM integration, Content generators |
| Phase 4 | 3 weeks | Upload system, Enhancement pipeline |
| Phase 5 | 3 weeks | Wizard & Expert UI modes |
| Phase 6 | 4 weeks | Interactive content, Analytics |
| **Total** | **19 weeks** | **Full platform** |

## Technical Implementation Details

### API Structure
```python
# API routes
/api/auth/          # Authentication endpoints
/api/courses/       # Course CRUD operations
/api/materials/     # Material management
/api/generate/      # Content generation
/api/workflow/      # Workflow state management
/api/export/        # Export functionality
```

### Frontend Architecture
```python
# Using FastHTML + HTMX
- Server-side rendering for better performance
- Progressive enhancement
- Minimal JavaScript
- Component-based architecture
- Real-time updates via SSE
```

### Security Considerations
- User data isolation
- API rate limiting
- Input sanitization
- Secure file handling
- LLM prompt injection prevention

## Phase 2 Enhancement: Git-Backed Storage Architecture

**Status**: Planned (Post-MVP)
**Timeline**: 13-19 weeks after current MVP completion
**Documentation**: [ADR-0013](../adr/0013-git-backed-content-storage.md) | [Git Migration Plan](GIT_MIGRATION_PLAN.md)

### Overview
After completing the current MVP implementation, the system will undergo a major architectural enhancement to migrate from database-centric content storage to a Git-backed architecture. This migration will provide:

- **85%+ storage reduction** through Git delta compression
- **Professional version control** with native Git features
- **Protection against LLM drift** via immutable commit history
- **Collaboration capabilities** for future team features
- **Advanced version management** with branching and merging

### Migration Strategy
The Git migration is designed as a **separate enhancement project** that:
- Does not block current MVP development
- Can be implemented incrementally alongside existing database storage
- Provides significant long-term benefits for scalability and collaboration
- Leverages proven Git technology instead of homemade version control

### Relationship to Current Implementation
- **Phase 1 (Current)**: Complete MVP with database storage
  - Tasks 8.6: Admin Dashboard
  - Tasks 10.1-10.4: Comprehensive testing
- **Phase 2 (Future)**: Git-backed storage migration
  - Migrate existing content to Git repositories
  - Replace homemade version control with native Git
  - Add collaboration and advanced diff features

## Current MVP Status

### Completed ✅
- **Task 8.4**: Task Management UI (Kanban board) ✅
- **Task 8.5**: Version History Browser (Visual diff interface) ✅
- Core system architecture and authentication
- LLM integration and content generation
- Material CRUD operations with basic version control
- Plugin system for content validation/remediation
- Import system for PDF/DOCX/PPTX files

### In Progress 🔄
- **Task 8.6**: Admin Dashboard (User management, settings)
- **Tasks 10.1-10.4**: Comprehensive testing (backend + frontend)

### Next Steps (Current MVP Completion)

1. **Complete Admin Dashboard** (Task 8.6)
   - User management interface
   - System settings and configuration
   - Security and permissions management

2. **Implement Comprehensive Testing** (Tasks 10.1-10.4)
   - Backend unit and integration tests
   - Frontend component and E2E tests
   - Test coverage and CI/CD pipeline

3. **MVP Launch** 
   - Production deployment
   - Documentation and user guides
   - Performance optimization

4. **Phase 2 Planning**
   - Git migration architecture finalization
   - Resource allocation for Git enhancement project

This roadmap provides a clear path from the current near-complete MVP to a full-featured curriculum creation platform with enterprise-grade version control capabilities.