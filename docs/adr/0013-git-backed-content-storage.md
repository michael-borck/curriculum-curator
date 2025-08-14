# 13. Git-Backed Content Storage Architecture

Date: 2025-01-14

## Status

Proposed (Phase 2 Enhancement)

## Context

The current curriculum curator system stores all content (lectures, worksheets, quizzes) in SQLite database using a homemade version control system. This approach has several limitations:

### Current Database-Centric Storage Problems

1. **Storage Inefficiency**: Each version stores complete content, leading to massive duplication
2. **Reimplementing Git**: Poorly replicating proven version control with `version`, `parent_version_id` fields
3. **Limited Features**: Basic diff functionality, no branching, merging, or advanced history
4. **LLM Vulnerability**: No protection against model drift or hallucinations corrupting content
5. **Database Bloat**: Large content stored as TEXT/JSON inflates SQLite database size
6. **Query Performance**: Large content fields slow down metadata queries

### Storage Analysis

Current material storage in `materials` table:
- `content` (JSON): Structured content data
- `raw_content` (TEXT): Raw markdown/HTML content
- `version` (INTEGER): Manual version tracking
- `parent_version_id` (UUID): Manual parent reference

Example storage inefficiency:
- 10 versions of 50KB lecture = 500KB stored (vs ~60KB with Git compression)
- 100 materials × 5 versions each = 25MB → 3MB with Git delta compression

## Decision

Migrate to a Git-backed content storage architecture that combines the efficiency and power of Git with database metadata management.

### Hybrid Architecture

**Git Repositories**: Content storage and versioning
- One Git repo per user workspace for content isolation
- Native Git versioning replaces homemade version control
- Professional diff, blame, and history capabilities
- Protection against LLM drift through immutable commit history

**Database**: Metadata and references only
- Material metadata (title, type, permissions, quality scores)
- Git commit references (`git_commit_hash`, `file_path`)
- User preferences and system configuration
- Relationships and foreign keys

### Proposed Structure

```
workspaces/
├── user_{uuid}/                 # Git repo per user workspace
│   ├── .git/                   # Git metadata and history
│   ├── courses/
│   │   └── {course_id}/
│   │       └── materials/
│   │           ├── lecture_001.md       # Raw content files
│   │           ├── lecture_001.json     # Structured metadata
│   │           ├── worksheet_002.md
│   │           └── quiz_003.md
│   ├── imports/                # Imported content staging
│   └── templates/              # User custom templates
├── shared/                     # System-wide shared resources
│   ├── templates/              # Default templates
│   └── examples/               # Example content
└── backups/                    # Git backup repositories
```

### Database Schema Changes

**Remove from `materials` table:**
- `content` (JSON) - Move to Git files
- `raw_content` (TEXT) - Move to Git files

**Add to `materials` table:**
- `git_commit_hash` (VARCHAR) - Reference to Git commit
- `file_path` (VARCHAR) - Path within Git repository
- `git_repo_id` (VARCHAR) - User workspace identifier

**Keep in `materials` table:**
- All metadata fields (title, description, type, etc.)
- Quality scores and validation results
- Timestamps and relationships
- Teaching philosophy and generation context

## Implementation Strategy

### Phase 1: Git Infrastructure (4-6 weeks)
1. **GitContentService**: Core Git operations wrapper using GitPython
2. **WorkspaceManager**: User Git repository lifecycle management
3. **ContentMigrator**: Database-to-Git migration utility
4. **Parallel Operation**: New Git backend alongside existing database storage

### Phase 2: Database Schema Migration (2-3 weeks)
1. Add new Git reference columns to materials table
2. Migrate existing content from database to Git repositories
3. Update all CRUD operations to use Git backend
4. Maintain backward compatibility during transition

### Phase 3: Version Control Integration (3-4 weeks)
1. Replace homemade versioning with Git commits
2. Implement Git-based diff viewing (native Git diff vs current library)
3. Add Git blame view for tracking changes (LLM vs human)
4. Support content branching for experimental materials

### Phase 4: Enhanced Features (4-6 weeks)
1. Collaborative editing with merge conflict resolution
2. Advanced history visualization using Git log graphs
3. Content backup/restore using Git remotes
4. Plugin integration with Git hooks for validation
5. Advanced diff tools (word-level, semantic diffs)

## Benefits

### Storage Efficiency
- **85-90% storage reduction** through Git delta compression
- **Faster queries** by removing large content from database
- **Scalable** - Git handles large repositories efficiently

### Version Control
- **Professional version control** with native Git tooling
- **Immutable history** protects against LLM hallucinations
- **Advanced diff capabilities** (line, word, semantic)
- **Branching and merging** for experimental content

### Future Capabilities
- **Real collaboration** - multiple users can work on same content
- **Conflict resolution** - standard Git merge workflows
- **Backup and sync** - Git remotes for distributed backup
- **Integration** - Leverage entire Git ecosystem (hooks, CI/CD)

### Developer Experience
- **Standard tooling** - Use familiar Git commands for debugging
- **Better debugging** - Git blame shows exact change attribution
- **Extensibility** - Git hooks for custom validation/processing

## Risks and Mitigation

### Complexity Risk
- **Risk**: Git operations more complex than database queries
- **Mitigation**: Comprehensive GitContentService abstraction layer

### Performance Risk
- **Risk**: Git operations might be slower than database queries
- **Mitigation**: Benchmarking, caching layer, async operations

### Data Integrity Risk
- **Risk**: Git repository corruption
- **Mitigation**: Regular repository validation, distributed backups

### Migration Risk
- **Risk**: Data loss during migration
- **Mitigation**: Complete backup strategy, parallel operation period

## Alternatives Considered

### Enhanced Database Storage
- Store diffs instead of full content
- Rejected: Still reimplementing Git poorly

### File-Based Storage (ADR-0005)
- Simple file storage with basic versioning
- Rejected: Limited collaboration features, need custom version control

### External Git Services
- Use GitHub/GitLab APIs for storage
- Rejected: Dependency on external services, network requirements

### Document Databases
- MongoDB with version tracking
- Rejected: Adds deployment complexity, still need custom versioning

## Implementation Notes

### Service Architecture
```python
class GitContentService:
    """Core Git operations for content management"""
    def create_material(self, user_id: str, content: str) -> str
    def update_material(self, user_id: str, material_id: str, content: str) -> str
    def get_material_history(self, user_id: str, material_id: str) -> List[GitCommit]
    def diff_versions(self, user_id: str, commit1: str, commit2: str) -> GitDiff

class WorkspaceManager:
    """User Git repository lifecycle management"""
    def create_workspace(self, user_id: str) -> GitRepo
    def clone_workspace(self, source_user: str, target_user: str) -> GitRepo
    def backup_workspace(self, user_id: str, remote_url: str) -> bool
```

### Migration Strategy
1. **Parallel Operation**: Run both database and Git storage simultaneously
2. **Content Export**: Batch export existing content to Git repositories
3. **Reference Update**: Update database records with Git commit references
4. **Validation**: Compare database vs Git content for consistency
5. **Cutover**: Switch to Git-only operations after validation
6. **Cleanup**: Remove old content columns after successful migration

### Performance Considerations
- **Lazy Loading**: Load content from Git only when needed
- **Caching**: Cache frequently accessed content in memory
- **Async Operations**: Use async Git operations for non-blocking I/O
- **Bulk Operations**: Batch multiple changes into single commits

## Success Metrics

### Storage Efficiency
- **Target**: 85%+ reduction in storage size
- **Measurement**: Compare database size before/after migration

### Performance
- **Target**: <200ms for content retrieval operations
- **Target**: <500ms for diff generation
- **Measurement**: Response time benchmarks

### Reliability
- **Target**: Zero data loss during migration
- **Target**: 99.9% uptime during parallel operation
- **Measurement**: Automated data integrity checks

## Timeline

**Total Estimated Effort**: 13-19 weeks

- **Phase 1**: 4-6 weeks (Git Infrastructure)
- **Phase 2**: 2-3 weeks (Schema Migration)  
- **Phase 3**: 3-4 weeks (Version Control Integration)
- **Phase 4**: 4-6 weeks (Enhanced Features)

**Prerequisites**: Complete current MVP (Task 8.6, Tests 10.1-10.4)

## References

- [Git Internals Documentation](https://git-scm.com/book/en/v2/Git-Internals)
- [GitPython Library](https://gitpython.readthedocs.io/)
- [ADR-0005: Hybrid Storage Approach](0005-hybrid-storage-approach.md)
- [SQLite vs Git Storage Benchmarks](#)

## Decision Rationale

This migration positions the curriculum curator for long-term success by:
1. **Solving current storage inefficiencies** (85%+ storage reduction)
2. **Providing professional version control** (native Git features)
3. **Protecting against LLM drift** (immutable Git history)
4. **Enabling future collaboration** (Git-based workflows)
5. **Leveraging proven technology** (Git's 20+ years of development)

The investment in Git-backed storage pays dividends through reduced storage costs, enhanced capabilities, and future-proofing for collaborative features.