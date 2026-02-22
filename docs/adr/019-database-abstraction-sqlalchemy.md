# 19. Database Abstraction with SQLAlchemy ORM

Date: 2025-12-01

## Status

Accepted

## Context

The Curriculum Curator needs a database strategy that balances:

1. **Development velocity**: Quick iteration during MVP phase
2. **Deployment flexibility**: Self-hosted users may have existing databases
3. **Maintainability**: Clear, readable data access code
4. **Performance**: Acceptable query performance for educational workloads
5. **Open source friendliness**: Contributors should find familiar patterns

### Deployment Scenarios

As an open-source project, we anticipate various deployment contexts:

| Scenario | Database Preference |
|----------|-------------------|
| Quick local setup | SQLite (zero config) |
| Small institution | SQLite or PostgreSQL |
| University IT department | PostgreSQL (existing infrastructure) |
| Cloud deployment | PostgreSQL, MySQL |
| Docker compose | PostgreSQL (included) |

### Developer Considerations

- **Primary maintainer** (Michael): Comfortable with raw SQL, SQLite
- **Potential contributors**: Likely familiar with ORMs (Django, SQLAlchemy)
- **Code readability**: ORM code more self-documenting than raw SQL strings

## Decision

Use **SQLAlchemy ORM** as the primary database abstraction layer, with SQLite as the default development/small deployment database.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                          │
│              (Services, API Routes)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLAlchemy ORM                             │
│            (Models, Relationships, Queries)                  │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         ┌────────┐   ┌──────────┐   ┌─────────┐
         │ SQLite │   │PostgreSQL│   │  MySQL  │
         │(default)│   │          │   │         │
         └────────┘   └──────────┘   └─────────┘
```

### Configuration

```python
# Default: SQLite (zero config)
DATABASE_URL=sqlite:///./curriculum_curator.db

# PostgreSQL (self-hosted with existing DB)
DATABASE_URL=postgresql://user:pass@localhost/curriculum

# MySQL (if required by institution)
DATABASE_URL=mysql://user:pass@localhost/curriculum
```

### Escape Hatches

For performance-critical queries or complex operations:

1. **SQLAlchemy Core**: Drop to SQL expression language (still portable)
2. **Raw SQL**: Use `session.execute(text(...))` for specific queries
3. **Database-specific**: Annotate with comments when using DB-specific features

```python
# Level 1: ORM (default, most readable)
users = session.query(User).filter(User.is_active == True).all()

# Level 2: Core (more control, still portable)
stmt = select(User).where(User.is_active == True)
users = session.execute(stmt).scalars().all()

# Level 3: Raw SQL (when needed, document why)
# NOTE: Using raw SQL for complex CTE query - see issue #123
result = session.execute(text("""
    WITH active_units AS (...)
    SELECT ...
"""))
```

## Consequences

### Positive

- **Database portability**: Switch databases via config, not code changes
- **Pythonic code**: Models are classes, queries are method chains
- **Self-documenting**: Relationships explicit in model definitions
- **Migrations**: Alembic handles schema evolution
- **Contributor friendly**: SQLAlchemy is widely known
- **Type hints**: Full typing support with SQLAlchemy 2.0

### Negative

- **Learning curve**: ORM patterns differ from raw SQL thinking
- **Query overhead**: ORM adds abstraction layer (minimal in practice)
- **N+1 queries**: Easy to accidentally create inefficient queries
- **Magic behavior**: Lazy loading can surprise developers

### Neutral

- **SQLite limitations**: Some features (full-text search, JSON) differ across DBs
- **Migration complexity**: Schema changes need Alembic migrations
- **Testing**: Need to consider DB state in tests

## Mitigations

### N+1 Query Prevention

```python
# Bad: N+1 queries
units = session.query(Unit).all()
for unit in units:
    print(unit.materials)  # Each access hits DB

# Good: Eager loading
units = session.query(Unit).options(
    selectinload(Unit.materials)
).all()
```

### Performance Monitoring

- Log slow queries in development
- Add query count assertions in tests
- Profile before optimizing

### SQLite Compatibility

- Avoid DB-specific features in core models
- Document any PostgreSQL-only features
- Test migrations on both SQLite and PostgreSQL

## Alternatives Considered

### Raw SQLite Only

- **Description**: Direct sqlite3 module, hand-written SQL
- **Pros**: No abstraction overhead, full control, maintainer familiarity
- **Rejected because**: Limits deployment options; less contributor-friendly; more boilerplate

### Django ORM

- **Description**: Use Django's ORM standalone or migrate to Django
- **Rejected because**: Would require Django dependency; overkill for API-only backend

### SQLModel

- **Description**: Pydantic + SQLAlchemy hybrid by FastAPI creator
- **Considered**: Good Pydantic integration
- **Rejected because**: Less mature; SQLAlchemy 2.0 has good typing; we already have SQLAlchemy

### Tortoise ORM

- **Description**: Async-first ORM inspired by Django
- **Rejected because**: Smaller ecosystem; SQLAlchemy async support is now mature

### No ORM (Query Builder Only)

- **Description**: Use SQLAlchemy Core without ORM models
- **Rejected because**: Loses relationship modeling; more verbose for common operations

## Implementation Notes

### Current State

- SQLAlchemy 2.0 with async support
- 33+ models implemented
- Alembic migrations configured
- SQLite default in development

### Adding PostgreSQL Support

```bash
# Install driver
pip install psycopg2-binary  # or asyncpg for async

# Update .env
DATABASE_URL=postgresql://user:pass@localhost/curriculum

# Run migrations
alembic upgrade head
```

### Model Conventions

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Unit(Base):
    __tablename__ = "units"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    owner: Mapped["User"] = relationship(back_populates="units")
    materials: Mapped[list["Material"]] = relationship(back_populates="unit")
```

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Migration Tool](https://alembic.sqlalchemy.org/)
- [FastAPI with SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [ADR-005: Hybrid Storage Approach](005-hybrid-storage-approach.md)
