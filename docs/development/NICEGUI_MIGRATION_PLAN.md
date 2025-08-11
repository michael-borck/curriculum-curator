# NiceGUI Migration Plan - Complete Rewrite Strategy

**Document Version**: 1.0  
**Date**: 2025-08-03  
**Status**: Active Implementation Plan  
**Related ADR**: [ADR-0012: Framework Migration](../adr/0012-framework-migration-fasthtml-to-nicegui.md)

## Executive Summary

This document outlines the complete migration strategy from FastHTML to NiceGUI framework, implemented as a fresh start rather than incremental migration. The plan includes detailed timelines, technical specifications, risk mitigation, and success criteria.

## Migration Rationale

### FastHTML Implementation Issues
- **Non-functional LLM integration** with placeholder implementations
- **UI/UX inconsistencies** and layout problems 
- **Development velocity constraints** due to manual styling requirements
- **Technical debt accumulation** with incomplete features throughout
- **Poor user experience** with styling issues and mobile responsiveness

### NiceGUI Advantages
- **Built-in Material Design components** for professional UI
- **Real-time WebSocket updates** for dynamic interfaces
- **Faster development** with declarative component approach
- **Better mobile responsiveness** out of the box
- **Comprehensive testing framework** for UI validation

## Implementation Strategy: Fresh Start

### Approach: Clean Slate Development
- **Archive existing FastHTML codebase** for reference
- **Start new NiceGUI implementation** from project foundation
- **Preserve business logic concepts** and architectural patterns
- **Focus on working functionality** over code preservation

### Rationale for Fresh Start
1. **Technical debt elimination**: Remove incomplete implementations and placeholders
2. **Framework optimization**: Build around NiceGUI strengths from the beginning  
3. **Faster delivery**: 4-6 weeks fresh start vs 8-12 weeks debugging existing code
4. **Better architecture**: Design components properly for NiceGUI patterns

## Detailed Implementation Plan

### Phase 1: Foundation & Setup (Days 1-3)

#### Day 1: Archive & Project Setup
**Tasks:**
- [x] Create `python-fasthtml` archive branch
- [x] Move FastHTML code to `reference-implementations/python-fasthtml-version/`
- [x] Create ADR-0012 documenting migration decision
- [x] Create this migration plan document
- [ ] Clean main branch of FastHTML code
- [ ] Initialize NiceGUI project structure

**Deliverables:**
- Complete FastHTML archive with documentation
- Clean main branch ready for NiceGUI development
- Project planning documentation

#### Days 2-3: Core Infrastructure
**Tasks:**
- [ ] Install NiceGUI and dependencies (`pip install nicegui`)
- [ ] Set up project structure based on NiceGUI best practices
- [ ] Port database schema and initialization scripts
- [ ] Configure environment variables and settings
- [ ] Set up development tooling (linting, testing, etc.)

**Deliverables:**
- Working NiceGUI development environment
- Database schema compatible with new framework
- Basic project structure and configuration

### Phase 2: Authentication & User Management (Week 1)

#### Days 4-5: Authentication Foundation
**Tasks:**
- [ ] Implement session-based authentication with NiceGUI
- [ ] Create login/logout flows with proper UI components
- [ ] Port password hashing and security measures
- [ ] Implement email verification with Brevo integration
- [ ] Add password reset functionality

**Technical Components:**
```python
# Example authentication structure
from nicegui import ui, app
from dataclasses import dataclass

@dataclass
class User:
    id: str
    email: str
    name: str
    is_admin: bool

class AuthManager:
    def login(self, email: str, password: str) -> User:
        # Implement authentication logic
        pass
    
    def create_session(self, user: User) -> str:
        # Session management
        pass

@ui.page('/login')
def login_page():
    with ui.card():
        ui.input('Email').props('outlined')
        ui.input('Password', password=True).props('outlined')
        ui.button('Login', on_click=handle_login)
```

#### Days 6-7: User Dashboard & Navigation
**Tasks:**
- [ ] Create responsive user dashboard layout
- [ ] Implement navigation structure with NiceGUI components
- [ ] Add user profile management interface
- [ ] Create course selection and creation entry points

**NiceGUI Components Used:**
- `ui.header()` for navigation
- `ui.card()` for content sections
- `ui.row()` and `ui.column()` for layout
- `ui.button()` for actions
- `ui.navigation()` for menu systems

### Phase 3: Admin Interface (Week 1 continued)

#### Days 8-10: Admin Dashboard
**Tasks:**
- [ ] Create admin-only access controls and routing
- [ ] Build user management interface with tables and actions
- [ ] Implement system monitoring dashboard
- [ ] Add admin navigation with tabs

**Admin Features:**
- User management (view, edit, promote/demote admin)
- System statistics with charts (`ui.chart()`)
- Configuration management
- Security status monitoring

### Phase 4: LLM Integration (Week 2)

#### Days 11-12: LLM Orchestrator Rebuild
**Tasks:**
- [ ] Implement multi-provider LLM orchestrator (OpenAI, Anthropic, Ollama)
- [ ] Add proper error handling and connection testing
- [ ] Implement usage tracking and cost monitoring
- [ ] Create real-time progress indicators for LLM operations

**Technical Architecture:**
```python
from nicegui import ui
import asyncio

class LLMOrchestrator:
    async def generate_content(self, prompt: str) -> str:
        # Implement with proper provider routing
        pass

async def generate_with_progress():
    progress = ui.circular_progress()
    result = await orchestrator.generate_content(prompt)
    progress.delete()
    ui.notify("Content generated successfully!")
```

#### Days 13-14: LLM Configuration Interfaces
**Tasks:**
- [ ] Create admin system-wide LLM configuration
- [ ] Build user API key management with encryption
- [ ] Add working test functionality with real responses
- [ ] Implement provider selection and model parameters

**UI Components:**
- Form controls with validation (`ui.select()`, `ui.slider()`)
- Encrypted storage interface
- Real-time testing with progress feedback
- Configuration persistence

### Phase 5: Content Generation (Week 3)

#### Days 15-17: Basic Content Generation
**Tasks:**
- [ ] Implement simple content generation to validate LLM connectivity
- [ ] Add content type selection (lectures, worksheets, quizzes)
- [ ] Create parameter controls for generation settings
- [ ] Add real-time progress tracking with WebSocket updates

#### Days 18-21: Teaching Philosophy Integration
**Tasks:**
- [ ] Port teaching philosophy detection system
- [ ] Create questionnaire interface with NiceGUI forms
- [ ] Implement style selection and results display
- [ ] Integrate teaching styles with content generation prompts

### Phase 6: Course Management (Week 4)

#### Days 22-24: Course Workflows
**Tasks:**
- [ ] Create course creation and management interfaces
- [ ] Implement file upload with progress indicators
- [ ] Add course organization and structure management
- [ ] Build course metadata editing forms

**NiceGUI File Upload:**
```python
@ui.page('/upload')
def upload_page():
    async def handle_upload(e):
        progress = ui.linear_progress()
        # Process uploaded file
        progress.value = 0.5  # Update progress
        # Complete processing
        progress.delete()
        ui.notify("Upload completed!")
    
    ui.upload(on_upload=handle_upload).props('accept=".pdf,.docx,.pptx"')
```

#### Days 25-28: Content Creation Modes
**Tasks:**
- [ ] Implement Wizard Mode with step-by-step interface
- [ ] Create Expert Mode with advanced controls
- [ ] Add batch generation capabilities
- [ ] Implement content review and editing interfaces

### Phase 7: Advanced Features (Week 5)

#### Days 29-31: Plugin System Integration
**Tasks:**
- [ ] Port plugin manager to NiceGUI interface
- [ ] Implement validation and remediation pipeline UI
- [ ] Create plugin configuration and management
- [ ] Add bulk operations and workflow management

#### Days 32-35: Export & Enhancement
**Tasks:**
- [ ] Implement export functionality with multiple formats
- [ ] Add content analysis and enhancement suggestions
- [ ] Create comparison interfaces for before/after content
- [ ] Build reporting and analytics dashboards

## Technical Specifications

### NiceGUI Project Structure
```
curriculum-curator/
├── main.py                     # NiceGUI application entry point
├── pyproject.toml             # Dependencies with NiceGUI
├── requirements.txt           # Production dependencies
├── .env.example              # Environment configuration
│
├── app/                      # Main application package
│   ├── __init__.py
│   ├── auth.py              # Authentication with NiceGUI sessions
│   ├── database.py          # Database models and operations
│   ├── config.py            # Configuration management
│   └── utils.py             # Utility functions
│
├── ui/                      # NiceGUI UI components
│   ├── __init__.py
│   ├── auth_pages.py        # Login, register, password reset
│   ├── dashboard.py         # User dashboard
│   ├── admin.py             # Admin interface
│   ├── course_management.py # Course creation and editing
│   ├── content_generation.py # Wizard and expert modes
│   └── components/          # Reusable UI components
│       ├── __init__.py
│       ├── layout.py        # Layout components
│       ├── forms.py         # Form components
│       └── charts.py        # Data visualization
│
├── core/                    # Business logic (ported from FastHTML)
│   ├── __init__.py
│   ├── llm_orchestrator.py  # LLM integration
│   ├── course_manager.py    # Course operations
│   ├── plugin_manager.py    # Plugin system
│   ├── teaching_philosophy.py # Teaching styles
│   └── security.py          # Security utilities
│
├── plugins/                 # Plugin system (unchanged)
│   ├── validators/
│   └── remediators/
│
├── tests/                   # NiceGUI testing
│   ├── conftest.py
│   ├── test_ui/            # UI component tests
│   ├── test_auth/          # Authentication tests
│   └── test_integration/   # Integration tests
│
├── docs/                   # Documentation (preserved)
└── data/                   # Database and uploads (preserved)
```

### Key Dependencies
```toml
[project]
dependencies = [
    "nicegui>=1.4.0",
    "fastapi>=0.104.0",        # NiceGUI backend
    "uvicorn>=0.24.0",         # Server
    "sqlite3",                 # Database
    "cryptography>=41.0.0",    # Encryption
    "aiohttp>=3.9.0",          # HTTP client
    "pydantic>=2.5.0",         # Data validation
    "textstat>=0.7.3",         # Text analysis
    "python-docx>=1.1.0",     # Document parsing
    "python-pptx>=0.6.23",    # PowerPoint parsing
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
    "basedpyright>=1.8.0",
]
```

### Database Schema (Preserved)
The existing SQLite schema will be preserved with minimal changes:
- `users` table for authentication
- `courses` table for course management
- `system_settings` table for configuration
- `llm_usage` table for tracking and costs
- `sessions` table for session management

### Configuration (Enhanced)
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server settings
    host: str = "localhost"
    port: int = 8080
    reload: bool = True
    
    # Database
    database_url: str = "sqlite:///data/curriculum.db"
    
    # Email service
    brevo_api_key: str
    sender_email: str = "noreply@curtin.edu.au"
    
    # Security
    session_secret: str
    encryption_key: str = None
    
    # LLM providers (optional)
    openai_api_key: str = None
    anthropic_api_key: str = None
    
    class Config:
        env_file = ".env"
```

## Component Mapping: FastHTML → NiceGUI

### Authentication Flow
```python
# FastHTML (old)
@rt("/login")
def post(req):
    form = await req.form()
    # Manual form handling
    return Page(...)

# NiceGUI (new)
@ui.page('/login')
def login_page():
    with ui.card():
        email = ui.input('Email').props('outlined')
        password = ui.input('Password', password=True).props('outlined')
        ui.button('Login', on_click=lambda: handle_login(email.value, password.value))
```

### Admin Dashboard
```python
# FastHTML (old)
def admin_dashboard():
    return Page(
        H1("Admin Panel"),
        Table(...)  # Manual table construction
    )

# NiceGUI (new)
@ui.page('/admin')
def admin_dashboard():
    with ui.header():
        ui.label('Admin Dashboard')
    
    with ui.tabs() as tabs:
        ui.tab('Users')
        ui.tab('Settings')
        ui.tab('System')
    
    with ui.tab_panels(tabs):
        with ui.tab_panel('Users'):
            ui.aggrid(users_data)  # Built-in data grid
```

### File Upload
```python
# FastHTML (old)
@rt("/upload")
async def post(req):
    # Manual file handling
    form = await req.form()
    file = form.get("file")
    return Response(...)

# NiceGUI (new)
def upload_interface():
    async def handle_upload(e):
        progress = ui.linear_progress()
        # File processing with real-time updates
        progress.value = 0.5
        await process_file(e.content)
        progress.delete()
        ui.notify("Upload completed!")
    
    ui.upload(on_upload=handle_upload).props('accept=".pdf,.docx"')
```

## Risk Assessment & Mitigation

### High Risk: Development Timeline
**Risk**: 5-week timeline may be optimistic for complete feature parity  
**Mitigation**: 
- Prioritize core functionality first (auth, LLM, basic course management)
- Implement advanced features incrementally
- Plan for potential 1-2 week extension if needed

### Medium Risk: Learning Curve
**Risk**: Team unfamiliarity with NiceGUI patterns  
**Mitigation**:
- Start with simple components and build complexity gradually
- Use NiceGUI documentation and examples extensively
- Plan learning time in early phases

### Medium Risk: Component Limitations
**Risk**: NiceGUI components may not support all required features  
**Mitigation**:
- Research component capabilities during planning
- Identify custom component needs early
- Plan for HTML/JavaScript integration where necessary

### Low Risk: Data Migration
**Risk**: Database schema incompatibility  
**Mitigation**:
- Database schema remains largely unchanged
- Test data migration with development database
- Plan rollback procedures

## Success Criteria & Milestones

### Week 1 Milestone: "Foundation Ready"
- ✅ Working authentication and user management
- ✅ Basic admin interface with user controls
- ✅ System monitoring and configuration
- ✅ Professional UI with consistent styling

### Week 2 Milestone: "LLM Integration"
- ✅ All LLM providers working with real responses
- ✅ Configuration interfaces functional
- ✅ Usage tracking and cost monitoring
- ✅ Real-time progress indicators

### Week 3 Milestone: "Content Generation"
- ✅ Basic content generation working
- ✅ Teaching philosophy integration
- ✅ Parameter controls and customization
- ✅ Content type selection and templates

### Week 4 Milestone: "Course Management"
- ✅ Complete course creation workflows
- ✅ File upload and processing
- ✅ Wizard and expert mode interfaces
- ✅ Course organization and management

### Week 5 Milestone: "Production Ready"
- ✅ Plugin system integrated
- ✅ Export functionality working
- ✅ All features tested and documented
- ✅ Performance optimized
- ✅ Ready for deployment

## Testing Strategy

### Component Testing
```python
# Example NiceGUI test
from nicegui.testing import Screen

def test_login_page(screen: Screen):
    @ui.page('/login')
    def login():
        ui.input('Email', placeholder='email')
        ui.button('Login')
    
    screen.open('/login')
    screen.should_contain('Email')
    screen.click('Login')
```

### Integration Testing
- Authentication flows with database
- LLM provider connections and responses
- File upload and processing pipelines
- Admin operations and user management

### Performance Testing
- Large file upload handling
- Multiple concurrent LLM requests
- Database query optimization
- UI responsiveness under load

## Deployment Considerations

### Development Environment
```bash
# Development setup
pip install -e ".[dev]"
python main.py --reload
```

### Production Deployment
```bash
# Production setup
pip install -e .
python main.py --host 0.0.0.0 --port 8080
```

### Docker Configuration
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
CMD ["python", "main.py", "--host", "0.0.0.0"]
```

## Quality Assurance

### Code Quality
- **Linting**: ruff for code formatting and style
- **Type Checking**: basedpyright for type safety
- **Testing**: pytest with NiceGUI testing framework
- **Coverage**: Target 80%+ test coverage

### User Experience
- **Responsive Design**: Test on multiple screen sizes
- **Accessibility**: Ensure keyboard navigation and screen reader support
- **Performance**: Sub-second response times for UI interactions
- **Browser Compatibility**: Test on major browsers

### Security
- **Authentication**: Secure session management
- **Input Validation**: Prevent injection attacks
- **File Upload**: Secure file handling and storage
- **API Security**: Rate limiting and validation

## Documentation Updates

### Technical Documentation
- [ ] Update API documentation for NiceGUI endpoints
- [ ] Revise deployment guides for new framework
- [ ] Create NiceGUI component usage examples
- [ ] Document testing procedures

### User Documentation
- [ ] Update getting started guide
- [ ] Revise configuration instructions
- [ ] Create new user interface guides
- [ ] Update troubleshooting documentation

## Rollback Plan

### Emergency Rollback
1. **Immediate**: Switch DNS/routing back to FastHTML version
2. **Database**: Restore from backup if schema changes occurred
3. **Code**: Deploy from `python-fasthtml` branch
4. **Communication**: Notify users of temporary rollback

### Rollback Triggers
- Critical functionality broken for >4 hours
- Data loss or corruption detected
- Security vulnerabilities discovered
- Performance degradation >50%

## Post-Migration Activities

### Week 6: Stabilization
- [ ] Bug fixes and performance optimization
- [ ] User feedback collection and analysis
- [ ] Documentation completion
- [ ] Deployment to production environment

### Long-term Maintenance
- [ ] Monitor performance and user satisfaction
- [ ] Plan feature enhancements based on user feedback
- [ ] Maintain NiceGUI framework updates
- [ ] Continue test coverage improvement

## Conclusion

This migration plan provides a comprehensive roadmap for transitioning from FastHTML to NiceGUI with a fresh start approach. The plan balances ambitious timeline goals with practical risk mitigation, ensuring delivery of a professional, functional application that addresses the critical issues with the current implementation.

Success depends on disciplined execution of the phase-by-phase plan, early identification and resolution of technical challenges, and maintaining focus on working functionality over perfect feature parity with incomplete specifications.

The resulting NiceGUI-based application will provide a solid foundation for future development, with improved user experience, faster development velocity, and better maintainability.