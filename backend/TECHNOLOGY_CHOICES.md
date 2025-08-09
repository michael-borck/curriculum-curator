# Technology Choices and Rationale

This document explains why we chose certain technologies that might seem like overkill for a small application but provide important benefits for future scaling and feature development.

## Database Stack

### SQLAlchemy + Alembic
**Why not direct SQLite?**
- **ORM Benefits**: Type safety, query building, relationship management
- **Database Agnostic**: Easy to switch from SQLite to PostgreSQL when scaling
- **Migration Tracking**: Alembic provides version control for database schema
- **Future Proof**: When the university adopts this, we can easily:
  - Switch to PostgreSQL/MySQL
  - Add read replicas
  - Implement sharding

### Current SQLite
- Perfect for development and small deployments
- Zero configuration
- Can handle thousands of users without issues
- Easy to backup (just copy the file)

## LLM Integration

### Langchain
**Why not direct API calls?**
- **Provider Abstraction**: Switch between OpenAI, Anthropic, Google, etc. without code changes
- **Future Features**:
  - Agentic workflows for automated course design
  - RAG (Retrieval Augmented Generation) for institution-specific content
  - Chain multiple models for quality control
  - Conversation memory for iterative content refinement
- **Built-in Features**: Token counting, streaming, retry logic, caching

## Security Decisions

### CSRF Protection (API-Friendly)
We implemented a nuanced approach:
- **JSON API calls**: Protected by CORS (no CSRF needed)
- **Form submissions**: Still require CSRF tokens
- **Rationale**: Modern SPAs use JSON APIs, but we might add traditional forms later

### Email Whitelist
- Supports both individual emails and entire domains
- Essential for university deployment (restrict to @university.edu)
- Prevents spam registrations
- Easy to manage through admin interface

## Authentication

### OAuth2PasswordRequestForm
- Industry standard for authentication
- Compatible with automatic API documentation
- Supports future OAuth2 provider integration
- Works with standard security audit tools

## Architecture Benefits

This "overengineered" approach provides:
1. **Easy scaling** when adopted institution-wide
2. **Standard patterns** that new developers understand
3. **Security best practices** built-in
4. **Future flexibility** for advanced features

## Technical Debt Acknowledgment

Yes, it's overkill for a prototype, but:
- The overhead is minimal
- The benefits appear immediately when scaling
- It's easier to start with good patterns than refactor later
- University IT departments expect enterprise patterns