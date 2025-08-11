# 5. Hybrid Database and Filesystem Storage

Date: 2025-08-01

## Status

Accepted

## Context

The application needs to store various types of data:
- User accounts and authentication
- Course metadata and structure
- Generated content (potentially large)
- Templates and configurations
- Session history
- Teaching preferences

We need a storage solution that is:
- Simple to deploy and maintain
- Efficient for both small metadata and large content
- Easy to backup and migrate
- Suitable for single-server deployment

## Decision

We will use a hybrid approach combining SQLite database with filesystem storage:

1. **SQLite Database** for:
   - User accounts and sessions
   - Course metadata
   - Material references (not content)
   - Settings and preferences
   - Audit trails

2. **Filesystem** for:
   - Generated content files (markdown, HTML, etc.)
   - Uploaded documents
   - Templates
   - Export artifacts
   - Large binary data

3. **Structure**:
   ```
   data/
   ├── curriculum.db          # SQLite database
   ├── courses/
   │   └── {course_id}/
   │       └── week_{n}/
   │           ├── lecture.md
   │           ├── worksheet.md
   │           └── meta.json
   ├── uploads/
   ├── templates/
   └── exports/
   ```

## Consequences

### Positive
- Simple deployment (no separate database server)
- Easy to backup (copy files and database)
- Efficient for large content (direct file access)
- Can use standard tools for file manipulation
- Natural organization of course materials

### Negative
- More complex than pure database solution
- Need to manage consistency between DB and files
- File permissions considerations
- Not suitable for multi-server deployment

### Neutral
- Requires careful transaction handling
- Need cleanup routines for orphaned files
- Migration strategy needed for scaling

## Alternatives Considered

### Pure SQLite
- Store everything in SQLite including BLOBs
- Rejected due to performance with large content

### PostgreSQL with JSONB
- Full-featured database with JSON support
- Rejected as overkill for single-server deployment

### Document Database (MongoDB)
- NoSQL approach for flexibility
- Rejected due to deployment complexity

### Cloud Storage (S3-compatible)
- Object storage for content files
- Rejected to maintain simple self-hosted solution

## Implementation Notes

- Use SQLAlchemy for database abstraction (future-proofing)
- Implement transactional file operations
- Create database references before writing files
- Regular cleanup of orphaned files
- Include file checksums in database for integrity

Example:
```python
class CourseManager:
    def save_material(self, course_id, week, content):
        # 1. Start DB transaction
        # 2. Create DB record with metadata
        # 3. Write file to filesystem
        # 4. Update DB record with file path
        # 5. Commit transaction
        pass
```

## References

- [SQLite Best Practices](https://www.sqlite.org/bestpractice.html)
- [ADR-0002](0002-fasthtml-web-framework.md) - Web framework choice
- [File Storage Patterns](#)