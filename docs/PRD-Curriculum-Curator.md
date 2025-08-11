# Product Requirements Document: Curriculum Curator
## Version 1.0 | December 2024

## Executive Summary

Curriculum Curator is a pedagogically-aware platform that enables educators to create, import, enhance, and manage course materials using AI assistance with human oversight. The system supports multiple workflows, from guided LRD-driven creation to quick generation, while maintaining educator control at every step.

### Core Value Proposition
- **For Educators**: Transform course creation from weeks to days while maintaining pedagogical integrity
- **Key Differentiator**: Human-in-the-loop AI assistance that respects teaching philosophy and provides oversight at each step
- **Primary Use Case**: Creating new courses from scratch with comprehensive materials

## User Personas

### Primary: Course Creator (Dr. Sarah Chen)
- **Role**: University lecturer creating a new course
- **Need**: Generate complete course materials aligned with teaching philosophy
- **Pain Points**: Time-consuming content creation, consistency across materials
- **Goal**: Create engaging, pedagogically-sound content efficiently

### Secondary: Course Enhancer (Prof. Michael Roberts)
- **Role**: Experienced educator with existing materials
- **Need**: Modernize and enhance legacy course content
- **Pain Points**: Outdated materials, inconsistent formatting, accessibility issues
- **Goal**: Improve existing materials while preserving what works

### Tertiary: Course Curator (Dr. Emily Johnson)
- **Role**: Department head overseeing multiple courses
- **Need**: Ensure consistency and quality across curriculum
- **Pain Points**: Varying quality, alignment with standards
- **Goal**: Standardize and validate course materials

## MVP Features (Phase 1)

### 1. Course Creation from Scratch
**Priority**: P0 (Critical)

#### Capabilities
- Create complete courses with all content types
- Support for 9 teaching philosophies
- Generate aligned materials across weeks/modules
- Maintain consistency throughout course

#### Content Types Supported
- Syllabus (with customizable templates)
- Lectures (slides, notes, scripts)
- Worksheets (exercises, problems)
- Quizzes (formative and summative)
- Labs (hands-on activities)
- Case Studies (real-world applications)
- Interactive HTML (self-contained pages)

#### Success Metrics
- Time to create complete course < 20 hours
- User satisfaction > 85%
- Content quality score > 80%

### 2. AI Enhancement of Imported Materials
**Priority**: P0 (Critical)

#### Capabilities
- Import multiple file formats (PDF, DOCX, PPTX, MD, HTML)
- Analyze and categorize existing content
- Identify gaps and improvement areas
- Enhance while preserving original intent
- Validate against learning objectives

#### Enhancement Types
- Readability improvements
- Structure optimization
- Accessibility compliance
- Interactive element addition
- Example generation
- Visual aid suggestions

#### Success Metrics
- Processing time < 5 minutes per document
- Enhancement acceptance rate > 70%
- Accessibility score improvement > 30%

### 3. Iterative Refinement Capability
**Priority**: P0 (Critical)

#### Capabilities
- Version control for all materials
- Track changes and improvements
- A/B testing of content variations
- Feedback incorporation
- Progressive enhancement

#### Iteration Features
- Compare versions side-by-side
- Rollback to previous versions
- Branch and merge content
- Annotation and commenting
- Change justification tracking

#### Success Metrics
- Average iterations per content: 2-3
- Time between iterations < 1 day
- Quality improvement per iteration > 15%

## Workflow Architecture

### Option C: Hybrid Workflow (Selected Approach)

#### Overview
Flexible system where LRD creation is optional but recommended. Users can:
1. Start with LRD for comprehensive planning
2. Jump directly to content generation for quick needs
3. Use wizard mode for guided creation

#### Workflow Paths

##### Path 1: LRD-Driven (Comprehensive)
```
1. Create LRD → Review materials, ask questions
2. Generate Task List → Break down into actionable items
3. Review & Approve → Human validates plan
4. Execute Tasks → Step-by-step with approval gates
5. Iterate & Refine → Continuous improvement
```

##### Path 2: Quick Generation (Agile)
```
1. Select Content Type → Choose what to create
2. Provide Context → Brief requirements
3. Generate Content → AI creates draft
4. Review & Edit → Human refinement
5. Save & Continue → Move to next item
```

##### Path 3: Wizard Mode (Guided)
```
1. Course Setup → Basic information
2. Teaching Philosophy → Select approach
3. Content Planning → Week-by-week outline
4. Material Generation → Automated creation
5. Review & Export → Final approval
```

### Human Oversight Points

#### Mandatory Gates
1. **LRD Approval**: Before task generation
2. **Task List Review**: Before execution begins
3. **Content Validation**: After each generation
4. **Final Review**: Before course publication

#### Optional Gates
1. **Sub-task Approval**: Granular control
2. **Enhancement Review**: For improvements
3. **Version Comparison**: For iterations
4. **Export Verification**: Format checking

## Data Architecture

### Core Entities

#### Learning Requirements Document (LRD)
```json
{
  "id": "uuid",
  "course_id": "reference",
  "version": "1.0",
  "status": "draft|approved|archived",
  "topic": {
    "week_unit": "string",
    "main_theme": "string",
    "duration": "timespan"
  },
  "learning_objectives": ["objective1", "objective2"],
  "target_audience": {},
  "structure": {
    "pre_class": {},
    "in_class": {},
    "post_class": {}
  },
  "constraints": {},
  "approval_history": [],
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### Course
```json
{
  "id": "uuid",
  "user_id": "reference",
  "title": "string",
  "code": "string",
  "teaching_philosophy": "enum",
  "language_preference": "en-AU|en-GB|en-US",
  "modules": [{
    "id": "uuid",
    "number": "integer",
    "title": "string",
    "type": "flipped|traditional|workshop",
    "duration": "timespan",
    "materials": ["material_ids"]
  }],
  "metadata": {
    "institution": "string",
    "semester": "string",
    "credits": "integer",
    "prerequisites": []
  },
  "status": "planning|active|complete",
  "created_at": "timestamp"
}
```

#### Content Material
```json
{
  "id": "uuid",
  "course_id": "reference",
  "module_id": "reference",
  "type": "lecture|worksheet|quiz|lab|case_study|interactive",
  "title": "string",
  "content": {
    "raw": "markdown/html",
    "structured": {},
    "metadata": {}
  },
  "version": "integer",
  "validation_results": [],
  "generation_context": {
    "llm_provider": "string",
    "prompt_template": "string",
    "teaching_style": "string"
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### Conversation History
```json
{
  "id": "uuid",
  "course_id": "reference",
  "session_id": "reference",
  "messages": [{
    "role": "user|assistant|system",
    "content": "string",
    "timestamp": "datetime",
    "context": {}
  }],
  "lrd_reference": "uuid",
  "task_references": ["task_ids"],
  "created_at": "timestamp"
}
```

### Database Schema

```sql
-- Core Tables
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    institution VARCHAR(255),
    teaching_philosophy VARCHAR(50),
    language_preference VARCHAR(10) DEFAULT 'en-AU',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE courses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    teaching_philosophy VARCHAR(50),
    language_preference VARCHAR(10),
    status VARCHAR(20) DEFAULT 'planning',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE lrds (
    id UUID PRIMARY KEY,
    course_id UUID REFERENCES courses(id),
    version VARCHAR(20),
    status VARCHAR(20) DEFAULT 'draft',
    content JSONB NOT NULL,
    approval_history JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE materials (
    id UUID PRIMARY KEY,
    course_id UUID REFERENCES courses(id),
    module_number INTEGER,
    type VARCHAR(50),
    title VARCHAR(255),
    content JSONB,
    version INTEGER DEFAULT 1,
    parent_version UUID REFERENCES materials(id),
    validation_results JSONB,
    generation_context JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_lists (
    id UUID PRIMARY KEY,
    lrd_id UUID REFERENCES lrds(id),
    course_id UUID REFERENCES courses(id),
    tasks JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    course_id UUID REFERENCES courses(id),
    session_id UUID,
    lrd_id UUID REFERENCES lrds(id),
    messages JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_courses_user ON courses(user_id);
CREATE INDEX idx_materials_course ON materials(course_id);
CREATE INDEX idx_materials_type ON materials(type);
CREATE INDEX idx_conversations_course ON conversations(course_id);
```

## Plugin Architecture

### Validator System

#### Base Validator Interface
```python
class BaseValidator:
    async def validate(content: str, context: Dict) -> ValidationResult
    def get_severity() -> Severity
    def get_category() -> str
```

#### Core Validators (MVP)
1. **ReadabilityValidator**: Flesch score, sentence complexity
2. **StructureValidator**: Heading hierarchy, section balance
3. **ObjectiveAlignmentValidator**: Content matches learning objectives
4. **AccessibilityValidator**: WCAG compliance, alt text
5. **LanguageValidator**: Spelling, grammar, regional preferences

#### Validation Pipeline
```
Content → Parallel Validation → Aggregate Results → Priority Issues → User Review
```

### Remediator System

#### Base Remediator Interface
```python
class BaseRemediator:
    async def remediate(content: str, issues: List[Issue]) -> RemediationResult
    def can_fix(issue: Issue) -> bool
    def get_priority() -> int
```

#### Core Remediators (MVP)
1. **ReadabilityEnhancer**: Simplify complex sentences
2. **StructureOptimizer**: Fix heading hierarchy
3. **AccessibilityFixer**: Add missing alt text
4. **ExampleGenerator**: Add relevant examples
5. **InteractivityAdder**: Convert static to interactive

## User Interface Requirements

### Navigation Structure
```
Dashboard
├── My Courses
│   ├── Course List/Grid
│   ├── Course Details
│   └── Course Materials
├── Create New
│   ├── From Scratch
│   ├── Import Materials
│   └── Use Template
├── Templates
│   ├── My Templates
│   └── Community Templates
└── Settings
    ├── Profile
    ├── Teaching Philosophy
    └── Preferences
```

### Key UI Components

#### Course Card
- Visual progress indicator
- Quick actions (Continue, Edit, Export)
- Status badges (Draft, Active, Complete)
- Last modified timestamp
- Material count by type

#### Content Generator Panel
- Split view (Configuration | Preview)
- Context awareness (previous/next content)
- Teaching style application
- Real-time validation feedback
- Save/regenerate options

#### Task Management View
- Kanban-style board
- Progress tracking
- Priority indicators
- Time estimates
- Approval status

### Responsive Design Requirements
- Desktop: Full feature set with multi-panel layouts
- Tablet: Simplified navigation, single panel focus
- Mobile: Read-only access, basic edits only

## Integration Requirements

### LLM Provider Support
- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude 3
- **Google**: Gemini Pro
- **Local**: Ollama support

### Import Formats
- **Documents**: PDF, DOCX, PPTX, ODT
- **Markup**: Markdown, HTML, LaTeX
- **Data**: CSV, JSON, XML
- **Media**: Images (context), Audio transcripts

### Export Formats
- **LMS**: SCORM, QTI, Common Cartridge
- **Documents**: PDF, DOCX, PPTX
- **Web**: Static HTML site, Jekyll
- **Archive**: ZIP with structure

## Performance Requirements

### Response Times
- Page load: < 2 seconds
- Content generation: < 30 seconds
- Import processing: < 1 minute per 10MB
- Export generation: < 2 minutes

### Scalability
- Support 1000+ concurrent users
- Handle courses with 50+ modules
- Process documents up to 100MB
- Store 10GB per user

### Reliability
- 99.9% uptime SLA
- Automatic save every 30 seconds
- Session recovery after disconnect
- Graceful degradation without AI

## Security & Compliance

### Data Protection
- User data isolation
- Encryption at rest and in transit
- GDPR compliance
- Regular backups

### Access Control
- Role-based permissions
- API rate limiting
- Session management
- Audit logging

### Content Security
- Input sanitization
- XSS prevention
- Prompt injection protection
- File type validation

## Success Metrics

### User Metrics
- Time to first course: < 1 hour
- Course completion rate: > 80%
- User retention (30 day): > 70%
- NPS score: > 40

### Quality Metrics
- Content validation pass rate: > 90%
- Accessibility score: > 85%
- Learning objective alignment: > 95%
- User edit rate: < 20%

### Business Metrics
- Cost per course created: < $10
- Support tickets per user: < 0.5
- Feature adoption rate: > 60%
- User growth rate: > 20% monthly

## Implementation Phases

### Phase 1: MVP (Weeks 1-8)
- Basic authentication and user management
- Course creation with LRD workflow
- Core content types (lecture, worksheet, quiz)
- Basic import/export
- Simple validation

### Phase 2: Enhancement (Weeks 9-12)
- Advanced content types (labs, interactive HTML)
- Plugin system for validators
- Version control
- Collaboration features
- Analytics dashboard

### Phase 3: Scale (Weeks 13-16)
- Performance optimization
- Advanced integrations
- Template marketplace
- API for third-party tools
- Mobile applications

### Phase 4: Intelligence (Weeks 17-20)
- Adaptive content generation
- Learning path optimization
- Outcome prediction
- Automated quality assurance
- Personalization engine

## Risk Analysis

### Technical Risks
- **LLM API Availability**: Mitigate with multiple providers
- **Content Quality**: Mitigate with validation pipeline
- **Performance at Scale**: Mitigate with caching, CDN

### User Risks
- **Learning Curve**: Mitigate with wizard mode
- **AI Trust**: Mitigate with transparency, control
- **Change Resistance**: Mitigate with import capabilities

### Business Risks
- **Cost Overruns**: Mitigate with usage limits
- **Competition**: Mitigate with unique features
- **Regulatory**: Mitigate with compliance framework

## Conclusion

Curriculum Curator represents a paradigm shift in course creation, combining AI efficiency with human expertise. By focusing on the three MVP features—course creation, material enhancement, and iterative refinement—while maintaining human oversight at every step, we deliver a platform that respects educator autonomy while dramatically reducing creation time.

The hybrid workflow approach ensures flexibility for different user preferences and use cases, while the comprehensive plugin architecture enables continuous improvement and customization. With clear success metrics and a phased implementation plan, Curriculum Curator is positioned to become the essential tool for modern educators.

## Appendices

### A. Glossary
- **LRD**: Learning Requirements Document
- **Teaching Philosophy**: Pedagogical approach preference
- **Module**: Discrete unit of course content
- **Validator**: Plugin that checks content quality
- **Remediator**: Plugin that fixes content issues

### B. User Stories
Available in separate document: user-stories.md

### C. Technical Specifications
Available in separate document: technical-specs.md

### D. Wireframes
Available in design folder: /docs/design/wireframes/

---
*Document Version: 1.0*
*Last Updated: December 2024*
*Status: Ready for Review*