# MVP Implementation Plan - Curriculum Curator

## Executive Summary
Focus on Docker deployment, export functionality, and essential admin features for MVP. Defer course wizard based on beta feedback.

## Architecture Decisions

### 1. Version Control Strategy - Git-Backed Content
**REPLACE Database Versioning with Git**
- **Remove**: Database version tracking (version, parent_version_id, is_latest fields)
- **Add**: Git repository for ALL content storage
- **Architecture**:
  - Database: Metadata only (title, type, git_path, permissions)
  - Git: All content files with full version history
  - Single system Git user (app process owner)
  - Web users separated by database permissions only
- **Benefits**: 
  - No reinventing version control
  - Real diffs, history, rollback
  - Efficient storage (Git deduplication)
  - No database bloat

### 2. Deployment Architecture
```
┌─────────────────────────────────────────┐
│         Docker Container                 │
│  ┌─────────────────────────────────┐    │
│  │   Frontend (Nginx + React)      │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │   Backend (FastAPI + Uvicorn)   │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │   Tools: Git, Quarto, Pandoc    │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │   SQLite DB (Volume Mount)      │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │   Git Repo (Volume Mount)       │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────┘
```

## Implementation Tasks

### Phase 0: Git-Backed Content Storage (Day 1)

#### Task 0.1: Remove Database Versioning
- Remove fields: version, parent_version_id, is_latest
- Add fields: git_path, current_commit
- Update Material model

#### Task 0.2: Implement Git Service
```python
class GitContentService:
    def save_content(path: str, content: str, user_email: str) -> str:
        # Save content to Git repo
        # Commit message: "Updated by: user@email.com"
        # Return commit hash
    
    def get_content(path: str, commit: str = None) -> str:
        # Get current or historical content
    
    def get_history(path: str) -> List[dict]:
        # Get commit history for file
    
    def diff(path: str, old_commit: str, new_commit: str) -> str:
        # Get diff between versions
```

#### Task 0.3: Update Material APIs
- Modify create/update endpoints to use GitContentService
- Add version history endpoint
- Add diff endpoint
- Ensure user isolation via database queries

#### Task 0.4: Initialize Git Repository
```bash
# In Docker container or app startup
git init /app/content
git config user.name "Curriculum Curator"
git config user.email "system@curriculum-curator.local"
```

### Phase 1: Docker & Export Infrastructure (Day 2)

#### Task 1.1: Create Multi-Stage Dockerfile
```dockerfile
# Stage 1: Frontend build
FROM node:18-alpine AS frontend-build
# Build React app

# Stage 2: Runtime
FROM python:3.11-slim
# Install Git, Quarto, Pandoc
# Copy frontend build
# Install Python deps
# Configure paths
```

#### Task 1.2: Export API Implementation
- **Endpoint**: `POST /api/export/{material_id}`
- **Body**: `{ "format": "pdf|docx|pptx|html|md", "options": {} }`
- **Process**:
  1. Fetch material content from DB
  2. Create temp Quarto project
  3. Generate output format
  4. Return file or download URL

#### Task 1.3: Quarto Service Integration
```python
class QuartoExportService:
    def export_to_pdf(material: Material) -> bytes
    def export_to_pptx(material: Material) -> bytes
    def export_to_docx(material: Material) -> bytes
    def export_to_html(material: Material) -> str
```

#### Task 1.4: Docker Compose Configuration
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data              # SQLite database
      - ./content:/app/content         # Git repository
      - ./exports:/app/exports         # Export output
    environment:
      - DATABASE_URL=sqlite:///app/data/curriculum.db
      - CONTENT_REPO_PATH=/app/content
      - GIT_PATH=/usr/bin/git
      - QUARTO_PATH=/usr/local/bin/quarto
```

### Phase 2: Admin Configuration (Days 2-3)

#### Task 2.1: First-User-Becomes-Admin Pattern
```python
# In auth.py registration endpoint
async def register(user_data: UserCreate, db: Session):
    user_count = db.query(User).count()
    if user_count == 0:
        user_data.role = "admin"
        user_data.is_superuser = True
    # Create user...
```

#### Task 2.2: System Configuration Model
```python
class SystemConfig(Base):
    __tablename__ = "system_config"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    category = Column(String)  # 'llm', 'tools', 'export'
    updated_at = Column(DateTime)
    updated_by = Column(GUID, ForeignKey("users.id"))
```

#### Task 2.3: Admin Configuration API
- `GET /api/admin/config` - Get all system settings
- `PUT /api/admin/config/llm` - Update LLM settings
- `PUT /api/admin/config/tools` - Update tool paths
- `POST /api/admin/config/test-llm` - Test LLM connection
- `POST /api/admin/config/test-tools` - Verify tool availability

#### Task 2.4: Admin UI Components
```typescript
// AdminDashboard.tsx additions
- <SystemSettings />
  - <LLMConfiguration />
  - <ToolPathConfiguration />
  - <ExportSettings />
- <UserManagement />  // Existing
- <SystemStatus />    // Existing
```

### Phase 3: Legal & Documentation (Days 3-4)

#### Task 3.1: Legal Pages Structure
```
/legal
  /licenses     - Open source attributions
  /ai-disclosure - AI usage transparency
  /disclaimer   - Content warnings
  /privacy      - Data handling
  /terms        - Terms of service
```

#### Task 3.2: License Attribution Generator
```python
# Script to generate LICENSE-THIRD-PARTY.md
def generate_license_file():
    # Parse package.json, pyproject.toml
    # Fetch license info
    # Generate attribution file
```

#### Task 3.3: Frontend Legal Components
```typescript
// LegalPage.tsx
const sections = {
  'Open Source': '/legal/licenses',
  'AI Disclosure': '/legal/ai-disclosure',
  'Content Disclaimer': '/legal/disclaimer'
}
```

### Phase 4: Testing & Documentation (Days 4-5)

#### Task 4.1: Docker Deployment Testing
- Build and run container
- Test all export formats
- Verify tool paths
- Test volume persistence

#### Task 4.2: Quick Start Guide
```markdown
# Quick Start
1. docker pull curriculum-curator:latest
2. docker run -p 8000:8000 curriculum-curator
3. Navigate to http://localhost:8000
4. First user becomes admin
```

## Deferred Features (Post-MVP)

### Course Wizard
- **Why Deferred**: Risk of over-automation, hallucinations
- **Current Solution**: Manual course creation with AI-assisted elements
- **Future**: Based on beta feedback, implement targeted wizards

### Custom PPTX Templates
- **Why Deferred**: Complex error handling needed
- **Current Solution**: Quarto default templates
- **Future**: Template upload with validation

### Advanced CI/CD
- **Why Deferred**: Docker sufficient for MVP
- **Current Solution**: Docker Hub deployment
- **Future**: GitHub Actions, automated testing

## Risk Mitigation

### 1. Tool Availability
- **Risk**: Git/Quarto not found
- **Mitigation**: Graceful fallback, clear error messages

### 2. Export Failures
- **Risk**: Large files, complex content
- **Mitigation**: Background jobs, progress tracking

### 3. Security
- **Risk**: Arbitrary command execution
- **Mitigation**: Sanitize inputs, use subprocess safely

## Success Metrics

- [ ] Docker container builds and runs
- [ ] Export works for all formats
- [ ] First user becomes admin
- [ ] LLM configuration persists
- [ ] Legal pages accessible
- [ ] No default credentials

## Timeline

- **Day 1**: Git-backed content storage
- **Day 2**: Docker + Export
- **Day 3**: Admin Configuration  
- **Day 4**: Legal + Documentation
- **Day 5**: Testing + Polish
- **Total**: 5 days to MVP

## Notes

1. **Git Integration**: REPLACES database versioning entirely
   - Database: metadata only (permissions, titles, references)
   - Git: all content storage and versioning
   - Single system user for Git (app process)
   - Web users isolated by database permissions
2. **Export Priority**: PDF > HTML > DOCX > PPTX
3. **Admin Features**: Essential only, enhance post-MVP
4. **Testing**: Focus on deployment, not coverage
5. **Documentation**: Quick start + deployment guide

## Key Architecture Points

- **No Git user management**: All commits by system user "Curriculum Curator"
- **User isolation**: Database controls who sees what content
- **Commit messages**: Include web user email for tracking ("Updated by: user@email.com")
- **No branching**: Simple linear history per file
- **Benefits**: Real diffs, history, rollback without database bloat