# Git-Backed Content Storage Migration Plan

## Overview

This document provides a detailed implementation plan for migrating from database-centric content storage to a Git-backed architecture. This migration is planned as a **Phase 2 enhancement** after MVP completion.

## Current State Analysis

### Current Architecture Problems
- **Storage Inefficiency**: 500KB for 10 versions vs 60KB with Git compression
- **Homemade Version Control**: Poorly reimplemented Git features
- **LLM Vulnerability**: No protection against model drift/hallucinations
- **Limited Collaboration**: No branching, merging, or real version control
- **Database Bloat**: Large content slows metadata queries

### Storage Metrics (Estimated)
- **Current**: ~25MB for 100 materials × 5 versions each
- **With Git**: ~3MB for same content (88% reduction)
- **Query Performance**: 2-5x faster without large TEXT/JSON columns

## Implementation Phases

## Phase 1: Git Infrastructure Setup (4-6 weeks)

### 1.1 Core Git Service Implementation (Week 1-2)

**GitContentService** - Core Git operations wrapper
```python
class GitContentService:
    """Centralized Git operations for content management"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.repo_cache = {}  # In-memory repo cache
    
    def create_material(self, user_id: str, material_id: str, content: str, 
                       metadata: dict) -> GitCommit:
        """Create new material with initial Git commit"""
        
    def update_material(self, user_id: str, material_id: str, content: str,
                       commit_message: str = None) -> GitCommit:
        """Update material content with new Git commit"""
        
    def get_material_content(self, user_id: str, commit_hash: str, 
                            file_path: str) -> str:
        """Retrieve content from specific Git commit"""
        
    def get_material_history(self, user_id: str, material_id: str) -> List[GitCommit]:
        """Get complete version history from Git log"""
        
    def diff_versions(self, user_id: str, commit1: str, commit2: str) -> GitDiff:
        """Generate diff between two commits using native Git"""
        
    def create_branch(self, user_id: str, branch_name: str, 
                     from_commit: str = None) -> GitBranch:
        """Create experimental branch for content development"""
```

**Key Features:**
- GitPython integration for Python Git operations
- Async support for non-blocking I/O operations
- Repository caching to avoid repeated Git operations
- Comprehensive error handling and logging
- Transaction support for atomic operations

### 1.2 Workspace Management (Week 2-3)

**WorkspaceManager** - User Git repository lifecycle
```python
class WorkspaceManager:
    """Manages Git repositories for user workspaces"""
    
    def create_workspace(self, user_id: str) -> GitRepo:
        """Initialize new Git repository for user"""
        workspace_path = self.workspace_root / f"user_{user_id}"
        repo = git.Repo.init(workspace_path)
        self._setup_repository_structure(repo)
        return repo
    
    def clone_workspace(self, source_user_id: str, target_user_id: str, 
                       materials: List[str] = None) -> GitRepo:
        """Clone specific materials from another user's workspace"""
        
    def backup_workspace(self, user_id: str, remote_url: str) -> bool:
        """Backup workspace to Git remote (GitHub, GitLab, etc.)"""
        
    def restore_workspace(self, user_id: str, remote_url: str) -> GitRepo:
        """Restore workspace from Git remote backup"""
        
    def archive_workspace(self, user_id: str) -> str:
        """Archive inactive workspace as Git bundle"""
```

**Directory Structure:**
```
workspaces/
├── user_{uuid}/                 # Individual user Git repositories
│   ├── .git/                   # Git metadata and history
│   ├── .gitignore              # Ignore temp files, caches
│   ├── courses/
│   │   └── {course_id}/
│   │       ├── materials/
│   │       │   ├── {material_id}.md        # Content files
│   │       │   ├── {material_id}.json      # Metadata
│   │       │   └── {material_id}.meta      # Git-specific metadata
│   │       └── exports/        # Generated exports
│   ├── imports/                # Staging area for imports
│   │   ├── processing/         # Files being processed
│   │   └── completed/          # Successfully imported
│   ├── templates/              # User custom templates
│   └── README.md              # Workspace documentation
├── shared/                     # System-wide resources
│   ├── templates/              # Default templates
│   ├── examples/               # Example content library
│   └── plugins/                # Shared plugin configurations
└── system/                     # System repositories
    ├── backups/                # Automated backups
    └── archives/               # Long-term storage
```

### 1.3 Content Migration Tools (Week 3-4)

**ContentMigrator** - Database to Git migration
```python
class ContentMigrator:
    """Handles migration from database storage to Git repositories"""
    
    def analyze_migration(self) -> MigrationAnalysis:
        """Analyze current database content for migration planning"""
        materials = db.query(Material).all()
        
        analysis = MigrationAnalysis(
            total_materials=len(materials),
            total_content_size=sum(len(m.raw_content or '') for m in materials),
            total_versions=sum(m.version for m in materials),
            estimated_git_size=self._estimate_git_size(materials),
            migration_time_estimate=self._estimate_migration_time(materials)
        )
        return analysis
    
    def migrate_user_content(self, user_id: str, dry_run: bool = True) -> MigrationResult:
        """Migrate all content for a specific user to Git"""
        
    def migrate_all_content(self, batch_size: int = 10) -> MigrationSummary:
        """Migrate all users' content in batches"""
        
    def validate_migration(self, user_id: str) -> ValidationResult:
        """Validate migrated content matches database content"""
        
    def rollback_migration(self, user_id: str) -> bool:
        """Rollback Git migration for a user (emergency only)"""
```

**Migration Process:**
1. **Analysis Phase**: Scan database content, estimate Git storage
2. **Validation Phase**: Dry-run migration, identify issues
3. **Migration Phase**: Batch migrate users, preserve history
4. **Verification Phase**: Compare database vs Git content
5. **Cleanup Phase**: Remove old content after verification

### 1.4 Parallel Operation Support (Week 4)

**Dual Storage Layer** - Support both database and Git during transition
```python
class ContentService:
    """Unified interface supporting both database and Git storage"""
    
    def __init__(self, use_git: bool = False):
        self.use_git = use_git
        self.db_service = DatabaseContentService()
        self.git_service = GitContentService()
    
    def get_material(self, material_id: str) -> Material:
        """Get material from appropriate storage backend"""
        if self.use_git:
            return self.git_service.get_material(material_id)
        return self.db_service.get_material(material_id)
    
    def update_material(self, material_id: str, content: str) -> Material:
        """Update material in both storage backends during transition"""
        # Update database
        db_result = self.db_service.update_material(material_id, content)
        
        # Update Git (if enabled)
        if self.use_git:
            git_result = self.git_service.update_material(material_id, content)
            # Store Git commit reference in database
            db_result.git_commit_hash = git_result.commit_hash
            db_result.file_path = git_result.file_path
        
        return db_result
```

## Phase 2: Database Schema Migration (2-3 weeks)

### 2.1 Schema Updates (Week 5)

**Add Git Reference Columns:**
```sql
-- Add Git reference columns to materials table
ALTER TABLE materials ADD COLUMN git_commit_hash VARCHAR(40);
ALTER TABLE materials ADD COLUMN file_path VARCHAR(500);
ALTER TABLE materials ADD COLUMN git_repo_id VARCHAR(100);
ALTER TABLE materials ADD COLUMN migration_status VARCHAR(20) DEFAULT 'pending';

-- Create indexes for Git references
CREATE INDEX idx_materials_git_commit ON materials(git_commit_hash);
CREATE INDEX idx_materials_git_repo ON materials(git_repo_id);
CREATE INDEX idx_materials_migration_status ON materials(migration_status);

-- Add workspace table for Git repository metadata
CREATE TABLE git_workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    repo_path VARCHAR(500) NOT NULL,
    last_commit_hash VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);
```

**SQLAlchemy Model Updates:**
```python
class Material(Base):
    # Existing fields...
    
    # Git reference fields
    git_commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    git_repo_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    migration_status: Mapped[str] = mapped_column(String(20), default='pending')
    
    # Keep content fields during transition (will be removed later)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)

class GitWorkspace(Base):
    __tablename__ = "git_workspaces"
    
    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("users.id"))
    repo_path: Mapped[str] = mapped_column(String(500))
    last_commit_hash: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default='active')
```

### 2.2 Data Migration Execution (Week 5-6)

**Migration Strategy:**
1. **User-by-user migration** to minimize risk
2. **Preserve all version history** in Git commits
3. **Maintain database references** during transition
4. **Validate each migration** before proceeding

**Migration Script:**
```python
async def migrate_database_to_git():
    """Execute the complete database to Git migration"""
    
    # Phase 1: Setup
    migration_log = setup_migration_logging()
    workspace_manager = WorkspaceManager()
    content_migrator = ContentMigrator()
    
    # Phase 2: Analysis
    analysis = content_migrator.analyze_migration()
    migration_log.info(f"Migration analysis: {analysis}")
    
    # Phase 3: User migration (batched)
    users = db.query(User).filter(User.is_active == True).all()
    
    for user in users:
        try:
            # Create Git workspace
            workspace = workspace_manager.create_workspace(user.id)
            
            # Migrate user's content
            result = await content_migrator.migrate_user_content(
                user.id, 
                dry_run=False
            )
            
            # Validate migration
            validation = content_migrator.validate_migration(user.id)
            if not validation.success:
                raise MigrationError(f"Validation failed: {validation.errors}")
            
            # Update migration status
            db.query(Material).filter(
                Material.course_id.in_(
                    db.query(Course.id).filter(Course.user_id == user.id)
                )
            ).update({"migration_status": "completed"})
            
            migration_log.info(f"Successfully migrated user {user.id}: {result}")
            
        except Exception as e:
            migration_log.error(f"Migration failed for user {user.id}: {e}")
            # Rollback on failure
            content_migrator.rollback_migration(user.id)
```

### 2.3 API Layer Updates (Week 6-7)

**Update Material Endpoints:**
```python
@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: UUID,
    git_service: GitContentService = Depends(get_git_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialResponse:
    """Get material content from Git repository"""
    
    # Get material metadata from database
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Get content from Git
    if material.git_commit_hash and material.file_path:
        content = await git_service.get_material_content(
            user_id=str(current_user.id),
            commit_hash=material.git_commit_hash,
            file_path=material.file_path
        )
    else:
        # Fallback to database content during migration
        content = material.raw_content or ""
    
    return MaterialResponse(
        id=str(material.id),
        content={"body": content},
        raw_content=content,
        git_commit_hash=material.git_commit_hash,
        file_path=material.file_path,
        # ... other fields
    )

@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: UUID,
    material_data: MaterialUpdate,
    git_service: GitContentService = Depends(get_git_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialResponse:
    """Update material content in Git repository"""
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Update content in Git
    commit = await git_service.update_material(
        user_id=str(current_user.id),
        material_id=str(material_id),
        content=material_data.content.body,
        commit_message=f"Update {material.title}"
    )
    
    # Update database references
    material.git_commit_hash = commit.hash
    material.file_path = commit.file_path
    material.updated_at = datetime.utcnow()
    
    # Keep database content in sync during transition
    material.raw_content = material_data.content.body
    
    db.commit()
    
    return MaterialResponse(
        id=str(material.id),
        git_commit_hash=material.git_commit_hash,
        file_path=material.file_path,
        # ... other fields
    )
```

## Phase 3: Version Control Integration (3-4 weeks)

### 3.1 Git-Based Version History (Week 8-9)

**Replace Homemade Versioning:**
```python
@router.get("/{material_id}/versions", response_model=List[MaterialVersionHistory])
async def get_material_versions(
    material_id: UUID,
    git_service: GitContentService = Depends(get_git_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaterialVersionHistory]:
    """Get version history from Git commits"""
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Get Git commit history
    commits = await git_service.get_material_history(
        user_id=str(current_user.id),
        material_id=str(material_id)
    )
    
    # Convert Git commits to version history
    version_history = []
    for i, commit in enumerate(commits):
        version_history.append(MaterialVersionHistory(
            id=commit.hash,
            version=len(commits) - i,  # Latest = highest version number
            created_at=commit.committed_date,
            change_summary=commit.message,
            author=commit.author.name,
            git_commit_hash=commit.hash,
            is_latest=(i == 0),  # First in list is latest
        ))
    
    return version_history

@router.get("/{material_id}/diff/{commit1}/{commit2}")
async def get_material_diff(
    material_id: UUID,
    commit1: str,
    commit2: str,
    git_service: GitContentService = Depends(get_git_service),
    current_user: User = Depends(get_current_user),
) -> MaterialDiff:
    """Get diff between two Git commits"""
    
    diff = await git_service.diff_versions(
        user_id=str(current_user.id),
        commit1=commit1,
        commit2=commit2
    )
    
    return MaterialDiff(
        old_commit=commit1,
        new_commit=commit2,
        diff_lines=diff.diff_lines,
        added_lines=diff.added_lines,
        removed_lines=diff.removed_lines,
        changed_files=diff.changed_files,
    )
```

### 3.2 Advanced Git Features (Week 9-10)

**Git Blame for Change Attribution:**
```python
@router.get("/{material_id}/blame")
async def get_material_blame(
    material_id: UUID,
    git_service: GitContentService = Depends(get_git_service),
    current_user: User = Depends(get_current_user),
) -> MaterialBlame:
    """Get line-by-line change attribution (Git blame)"""
    
    blame_info = await git_service.blame_material(
        user_id=str(current_user.id),
        material_id=str(material_id)
    )
    
    # Identify LLM vs human changes
    annotated_lines = []
    for line in blame_info.lines:
        is_llm_generated = 'llm-generated' in line.commit.message.lower()
        annotated_lines.append(BlameAnnotation(
            line_number=line.number,
            content=line.content,
            commit_hash=line.commit.hash,
            author=line.commit.author,
            commit_date=line.commit.date,
            commit_message=line.commit.message,
            is_llm_generated=is_llm_generated,
        ))
    
    return MaterialBlame(
        material_id=str(material_id),
        annotated_lines=annotated_lines,
        llm_percentage=sum(1 for l in annotated_lines if l.is_llm_generated) / len(annotated_lines) * 100
    )
```

**Content Branching for Experiments:**
```python
@router.post("/{material_id}/branches")
async def create_material_branch(
    material_id: UUID,
    branch_data: BranchCreate,
    git_service: GitContentService = Depends(get_git_service),
    current_user: User = Depends(get_current_user),
) -> MaterialBranch:
    """Create experimental branch for content development"""
    
    branch = await git_service.create_branch(
        user_id=str(current_user.id),
        branch_name=f"experiment-{material_id}-{branch_data.name}",
        from_commit=branch_data.from_commit
    )
    
    return MaterialBranch(
        name=branch.name,
        commit_hash=branch.head_commit,
        created_at=datetime.utcnow(),
        description=branch_data.description,
    )

@router.post("/{material_id}/merge")
async def merge_material_branch(
    material_id: UUID,
    merge_data: BranchMerge,
    git_service: GitContentService = Depends(get_git_service),
    current_user: User = Depends(get_current_user),
) -> MergeResult:
    """Merge experimental branch back to main"""
    
    result = await git_service.merge_branch(
        user_id=str(current_user.id),
        source_branch=merge_data.source_branch,
        target_branch="main",
        merge_message=merge_data.message
    )
    
    if result.conflicts:
        return MergeResult(
            success=False,
            conflicts=result.conflicts,
            merge_commit=None,
        )
    
    # Update database with new commit
    material = db.query(Material).filter(Material.id == material_id).first()
    material.git_commit_hash = result.merge_commit.hash
    material.updated_at = datetime.utcnow()
    db.commit()
    
    return MergeResult(
        success=True,
        conflicts=[],
        merge_commit=result.merge_commit.hash,
    )
```

### 3.3 Enhanced Diff Tools (Week 10-11)

**Semantic Diff for Educational Content:**
```python
class SemanticDiffService:
    """Generate semantic diffs for educational content"""
    
    def generate_semantic_diff(self, old_content: str, new_content: str) -> SemanticDiff:
        """Generate semantic diff highlighting educational changes"""
        
        # Extract learning objectives
        old_objectives = self.extract_learning_objectives(old_content)
        new_objectives = self.extract_learning_objectives(new_content)
        
        # Extract key concepts
        old_concepts = self.extract_key_concepts(old_content)
        new_concepts = self.extract_key_concepts(new_content)
        
        # Extract examples
        old_examples = self.extract_examples(old_content)
        new_examples = self.extract_examples(new_content)
        
        return SemanticDiff(
            objective_changes=self.diff_lists(old_objectives, new_objectives),
            concept_changes=self.diff_lists(old_concepts, new_concepts),
            example_changes=self.diff_lists(old_examples, new_examples),
            structural_changes=self.analyze_structure_changes(old_content, new_content),
        )
    
    def extract_learning_objectives(self, content: str) -> List[str]:
        """Extract learning objectives from content"""
        # Pattern matching for common objective formats
        patterns = [
            r"(?:Learning Objectives?|Objectives?)[:\n]\s*(.+?)(?:\n\n|\n[A-Z])",
            r"(?:Students will|Learners will|You will)[:\s]+(.+?)(?:\n\n|\n[A-Z])",
            r"(?:By the end|After this)[^.]+\.(.+?)(?:\n\n|\n[A-Z])",
        ]
        # Implementation...
```

## Phase 4: Enhanced Features (4-6 weeks)

### 4.1 Collaborative Editing (Week 12-14)

**Multi-User Git Workflows:**
```python
class CollaborationService:
    """Handle collaborative editing with Git workflows"""
    
    async def share_material(self, material_id: str, target_user_id: str, 
                           permissions: SharePermissions) -> ShareResult:
        """Share material with another user via Git"""
        
        # Create shared branch in target user's workspace
        source_workspace = self.workspace_manager.get_workspace(self.current_user.id)
        target_workspace = self.workspace_manager.get_workspace(target_user_id)
        
        # Cherry-pick commits for specific material
        commits = source_workspace.get_material_commits(material_id)
        for commit in commits:
            target_workspace.cherry_pick(commit)
        
        # Create collaboration metadata
        collaboration = Collaboration(
            material_id=material_id,
            owner_id=self.current_user.id,
            collaborator_id=target_user_id,
            permissions=permissions,
            shared_at=datetime.utcnow(),
        )
        db.add(collaboration)
        
        return ShareResult(success=True, collaboration=collaboration)
    
    async def sync_collaboration(self, collaboration_id: str) -> SyncResult:
        """Sync changes between collaborating users"""
        
        collaboration = db.query(Collaboration).filter_by(id=collaboration_id).first()
        
        # Fetch changes from both users
        owner_workspace = self.workspace_manager.get_workspace(collaboration.owner_id)
        collaborator_workspace = self.workspace_manager.get_workspace(collaboration.collaborator_id)
        
        # Identify conflicting changes
        conflicts = self.detect_conflicts(owner_workspace, collaborator_workspace)
        
        if conflicts:
            return SyncResult(success=False, conflicts=conflicts)
        
        # Auto-merge compatible changes
        merge_result = self.auto_merge_changes(owner_workspace, collaborator_workspace)
        
        return SyncResult(success=True, merge_commit=merge_result.commit_hash)
```

**Conflict Resolution Interface:**
```python
@router.get("/collaborations/{collaboration_id}/conflicts")
async def get_collaboration_conflicts(
    collaboration_id: UUID,
    collaboration_service: CollaborationService = Depends(get_collaboration_service),
) -> List[MergeConflict]:
    """Get merge conflicts for collaborative material"""
    
    conflicts = await collaboration_service.get_conflicts(collaboration_id)
    
    return [
        MergeConflict(
            file_path=conflict.file_path,
            conflict_markers=conflict.markers,
            our_version=conflict.our_content,
            their_version=conflict.their_content,
            base_version=conflict.base_content,
            resolution_suggestions=conflict.suggestions,
        )
        for conflict in conflicts
    ]

@router.post("/collaborations/{collaboration_id}/resolve")
async def resolve_collaboration_conflicts(
    collaboration_id: UUID,
    resolutions: List[ConflictResolution],
    collaboration_service: CollaborationService = Depends(get_collaboration_service),
) -> ResolveResult:
    """Resolve merge conflicts and complete collaboration sync"""
    
    result = await collaboration_service.resolve_conflicts(
        collaboration_id, 
        resolutions
    )
    
    return ResolveResult(
        success=result.success,
        merge_commit=result.merge_commit,
        resolved_conflicts=len(resolutions),
    )
```

### 4.2 Advanced History Visualization (Week 14-15)

**Git Log Graph Visualization:**
```python
@router.get("/{material_id}/history/graph")
async def get_material_history_graph(
    material_id: UUID,
    git_service: GitContentService = Depends(get_git_service),
    current_user: User = Depends(get_current_user),
) -> HistoryGraph:
    """Get Git history as visual graph data"""
    
    graph_data = await git_service.get_history_graph(
        user_id=str(current_user.id),
        material_id=str(material_id)
    )
    
    # Convert Git graph to frontend-friendly format
    nodes = []
    edges = []
    
    for commit in graph_data.commits:
        # Identify commit type (creation, edit, merge, LLM-generated)
        commit_type = classify_commit_type(commit)
        
        nodes.append(HistoryNode(
            id=commit.hash,
            label=commit.message[:50],
            commit_date=commit.date,
            author=commit.author,
            commit_type=commit_type,
            is_llm_generated='llm-generated' in commit.message.lower(),
        ))
        
        for parent in commit.parents:
            edges.append(HistoryEdge(
                source=parent.hash,
                target=commit.hash,
                edge_type='parent',
            ))
    
    return HistoryGraph(
        nodes=nodes,
        edges=edges,
        branches=graph_data.branches,
        tags=graph_data.tags,
    )
```

### 4.3 Backup and Sync (Week 15-16)

**Git Remote Integration:**
```python
class BackupService:
    """Handle Git-based backup and synchronization"""
    
    def setup_remote_backup(self, user_id: str, remote_config: RemoteConfig) -> BackupSetup:
        """Setup automatic backup to Git remote"""
        
        workspace = self.workspace_manager.get_workspace(user_id)
        
        # Add remote repository
        remote = workspace.create_remote(
            name=remote_config.name,
            url=remote_config.url,
            credentials=remote_config.credentials
        )
        
        # Setup automatic push hooks
        hook_script = self.generate_push_hook(remote_config)
        workspace.add_hook('post-commit', hook_script)
        
        # Initial push
        workspace.push(remote.name, 'main')
        
        return BackupSetup(
            remote_name=remote.name,
            remote_url=remote.url,
            auto_push_enabled=True,
            last_backup=datetime.utcnow(),
        )
    
    async def sync_from_remote(self, user_id: str, remote_name: str) -> SyncResult:
        """Sync workspace from Git remote"""
        
        workspace = self.workspace_manager.get_workspace(user_id)
        
        # Fetch latest changes
        workspace.fetch(remote_name)
        
        # Check for conflicts
        merge_result = workspace.merge(f"{remote_name}/main")
        
        if merge_result.conflicts:
            return SyncResult(
                success=False,
                conflicts=merge_result.conflicts,
                changes_pulled=0,
            )
        
        # Update database references for changed materials
        await self.update_database_references(workspace, merge_result.changed_files)
        
        return SyncResult(
            success=True,
            conflicts=[],
            changes_pulled=len(merge_result.changed_files),
        )
```

### 4.4 Plugin Integration with Git Hooks (Week 16-17)

**Git Hooks for Content Validation:**
```python
class GitHookManager:
    """Manage Git hooks for content validation and processing"""
    
    def setup_validation_hooks(self, workspace_path: str):
        """Setup Git hooks for automatic content validation"""
        
        # Pre-commit hook: Validate content before commit
        pre_commit_script = self.generate_pre_commit_hook()
        self.install_hook(workspace_path, 'pre-commit', pre_commit_script)
        
        # Post-commit hook: Run post-processing
        post_commit_script = self.generate_post_commit_hook()
        self.install_hook(workspace_path, 'post-commit', post_commit_script)
    
    def generate_pre_commit_hook(self) -> str:
        """Generate pre-commit hook script for validation"""
        return """#!/bin/bash
        # Pre-commit hook for content validation
        
        # Get list of changed files
        changed_files=$(git diff --cached --name-only --diff-filter=ACM)
        
        # Validate each changed material file
        for file in $changed_files; do
            if [[ $file == *.md ]]; then
                # Run spell checker
                python -m curriculum_curator.plugins.spell_checker "$file"
                if [ $? -ne 0 ]; then
                    echo "Spell check failed for $file"
                    exit 1
                fi
                
                # Run grammar validator  
                python -m curriculum_curator.plugins.grammar_validator "$file"
                if [ $? -ne 0 ]; then
                    echo "Grammar validation failed for $file"
                    exit 1
                fi
                
                # Run accessibility validator
                python -m curriculum_curator.plugins.accessibility_validator "$file"
                if [ $? -ne 0 ]; then
                    echo "Accessibility validation failed for $file"
                    exit 1
                fi
            fi
        done
        
        echo "All validations passed"
        exit 0
        """
    
    def generate_post_commit_hook(self) -> str:
        """Generate post-commit hook for post-processing"""
        return """#!/bin/bash
        # Post-commit hook for content post-processing
        
        # Get the latest commit hash
        commit_hash=$(git rev-parse HEAD)
        
        # Update database with new commit reference
        python -m curriculum_curator.services.git_sync_service update_commit_references "$commit_hash"
        
        # Generate analytics
        python -m curriculum_curator.services.analytics_service process_commit "$commit_hash"
        
        # Auto-backup if configured
        if [ -f .auto_backup_enabled ]; then
            git push origin main
        fi
        """
```

## Migration Testing Strategy

### Unit Tests
```python
class TestGitContentService:
    def test_create_material(self):
        """Test creating new material in Git"""
        
    def test_update_material(self):
        """Test updating existing material"""
        
    def test_get_material_history(self):
        """Test retrieving Git commit history"""
        
    def test_diff_versions(self):
        """Test generating diffs between commits"""

class TestContentMigrator:
    def test_migrate_user_content(self):
        """Test migrating single user's content"""
        
    def test_migration_validation(self):
        """Test validating migrated content"""
        
    def test_rollback_migration(self):
        """Test rolling back failed migration"""
```

### Integration Tests
```python
class TestGitMigrationIntegration:
    def test_full_migration_workflow(self):
        """Test complete migration from database to Git"""
        
    def test_parallel_operation(self):
        """Test dual storage during transition period"""
        
    def test_api_endpoints_with_git(self):
        """Test API endpoints using Git storage"""
```

### Performance Benchmarks
```python
class TestGitPerformance:
    def test_storage_efficiency(self):
        """Benchmark storage size: database vs Git"""
        
    def test_read_performance(self):
        """Benchmark content retrieval speed"""
        
    def test_write_performance(self):
        """Benchmark content update speed"""
        
    def test_diff_performance(self):
        """Benchmark diff generation speed"""
```

## Risk Mitigation

### Data Integrity
- **Complete backups** before migration
- **Parallel operation** during transition
- **Validation checks** at each step
- **Rollback procedures** for failures

### Performance
- **Benchmarking** before/after migration
- **Caching layer** for frequently accessed content
- **Async operations** for non-blocking I/O
- **Repository optimization** (Git GC, pack files)

### Operational
- **Monitoring** Git repository health
- **Automated backups** to Git remotes
- **Repository maintenance** (cleanup, optimization)
- **User training** on new features

## Success Metrics

### Storage Efficiency
- **Target**: 85%+ reduction in storage size
- **Current**: ~25MB for 100 materials × 5 versions
- **Expected**: ~3MB with Git compression

### Performance
- **Content retrieval**: <200ms (vs current ~150ms)
- **Diff generation**: <500ms (vs current ~1000ms)
- **Version history**: <300ms (vs current ~800ms)

### Feature Completeness
- **Git-based version control**: Native diff, blame, history
- **Collaborative editing**: Branching, merging, conflict resolution
- **Backup and sync**: Git remotes, automated backup
- **Enhanced visualization**: Git graph, timeline views

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 4-6 weeks | Git infrastructure, migration tools |
| Phase 2 | 2-3 weeks | Database schema, data migration |
| Phase 3 | 3-4 weeks | Version control integration |
| Phase 4 | 4-6 weeks | Advanced features, collaboration |
| **Total** | **13-19 weeks** | **Complete Git-backed architecture** |

**Prerequisites**: Complete current MVP (Task 8.6: Admin Dashboard, Tests 10.1-10.4)

This migration transforms the curriculum curator from a basic content management system into a professional, Git-backed educational content platform with enterprise-grade version control and collaboration capabilities.