# Architecture Overview

The Curriculum Curator is built on a modular architecture that separates concerns while maintaining simplicity. This document provides a high-level overview of the system architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                           │
│  ┌─────────────────┐                  ┌─────────────────┐  │
│  │   Wizard Mode   │                  │   Expert Mode   │  │
│  └─────────────────┘                  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │ HTMX
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastHTML Server                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Route Handlers                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │   Home   │  │  Wizard  │  │     Expert       │ │   │
│  │  │  Routes  │  │  Routes  │  │     Routes       │ │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────▼─────────────────────────────┐ │
│  │                    Core Services                       │ │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────┐    │ │
│  │  │  Auth   │  │  Course  │  │    Teaching      │    │ │
│  │  │ Manager │  │ Manager  │  │   Philosophy     │    │ │
│  │  └─────────┘  └──────────┘  └──────────────────┘    │ │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────┐    │ │
│  │  │ Plugin  │  │ Content  │  │    Session       │    │ │
│  │  │ Manager │  │Generator │  │    Manager       │    │ │
│  │  └─────────┘  └──────────┘  └──────────────────┘    │ │
│  └───────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌─────────────────────────▼─────────────────────────────┐ │
│  │                   Plugin System                        │ │
│  │  ┌──────────────────┐     ┌────────────────────────┐ │ │
│  │  │    Validators    │     │     Remediators        │ │ │
│  │  │ ┌──────────────┐ │     │ ┌────────────────────┐ │ │ │
│  │  │ │ Readability  │ │     │ │ Sentence Splitter  │ │ │ │
│  │  │ │ Structure    │ │     │ │ Format Corrector   │ │ │ │
│  │  │ │ Grammar      │ │     │ │ Style Adjuster     │ │ │ │
│  │  │ └──────────────┘ │     │ └────────────────────┘ │ │ │
│  │  └──────────────────┘     └────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage                            │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │  SQLite (DB)    │         │   Filesystem (Content)   │   │
│  │  - Users        │         │   - Course materials     │   │
│  │  - Courses      │         │   - Generated content    │   │
│  │  - Sessions     │         │   - Templates            │   │
│  │  - Settings     │         │   - Uploads              │   │
│  └─────────────────┘         └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### FastHTML Server
The main web server built with FastHTML, handling HTTP requests and serving HTML responses with HTMX for interactivity.

### Route Handlers
- **Home Routes**: Landing page and mode selection
- **Wizard Routes**: Step-by-step content creation flow
- **Expert Routes**: Advanced single-page interface
- **API Routes**: RESTful endpoints for data operations

### Core Services

#### Auth Manager
Handles user authentication and session management:
- User registration and login
- Session token management
- Password hashing (PBKDF2)

#### Course Manager
Manages course lifecycle and content:
- Course CRUD operations
- Material organization by week
- Progress tracking

#### Teaching Philosophy
Implements pedagogical awareness:
- 9 teaching styles with indicators
- Style detection questionnaire
- LLM prompt adaptation

#### Plugin Manager
Coordinates validation and remediation:
- Plugin discovery and registration
- Orchestrates validation pipeline
- Manages remediation strategies

#### Content Generator
Handles content creation (planned):
- LLM integration
- Streaming response handling
- Template-based generation

### Plugin System

#### Validators
Modules that check content quality:
- **Readability**: Flesch scores, sentence complexity
- **Structure**: Document organization
- **Grammar**: Language correctness
- Each validator returns issues with severity levels

#### Remediators
Modules that fix identified issues:
- **AutoFix**: Automated corrections (formatting, splitting)
- **LLM-Assisted**: AI-powered rewrites
- **Workflow**: Human-in-the-loop processes

### Data Storage

#### SQLite Database
Structured data storage:
- Lightweight, zero-configuration
- ACID compliance
- Perfect for single-server deployment

#### Filesystem
Content and asset storage:
- Organized directory structure
- Direct file access for performance
- Easy backup and migration

## Design Principles

### 1. Simplicity First
- Single Python codebase
- Minimal dependencies
- Clear, understandable architecture

### 2. Progressive Enhancement
- Core functionality works without JavaScript
- HTMX adds interactivity
- Graceful degradation

### 3. Modular Design
- Plugins for extensibility
- Clear interfaces between components
- Loose coupling

### 4. Pedagogical Awareness
- Teaching philosophy influences all content
- Respects diverse educational approaches
- Evidence-based practices

### 5. User-Centric
- Dual UI modes for different expertise levels
- Clear feedback and progress indication
- Accessible design

## Data Flow

### Content Creation Flow
1. User selects teaching style (or detected via quiz)
2. User inputs course requirements
3. System generates prompts adapted to teaching style
4. LLM generates content
5. Validators check quality
6. Remediators fix issues (if configured)
7. Content saved to filesystem with DB references
8. User can export in various formats

### Validation Pipeline
1. Content submitted for validation
2. Plugin Manager loads configured validators
3. Each validator analyzes content
4. Issues aggregated with severity levels
5. Remediation suggested based on issues
6. User chooses automatic or manual remediation

## Security Considerations

- Password hashing with salt
- Session-based authentication
- Input validation and sanitization
- File upload restrictions
- No direct file system access from web

## Scalability Considerations

Current architecture is designed for single-server deployment. Future scaling options:
- PostgreSQL for multi-user scenarios
- Redis for session storage
- S3-compatible storage for content
- Load balancing with sticky sessions

## Technology Stack

- **Backend**: Python 3.12+
- **Web Framework**: FastHTML
- **Database**: SQLite
- **Frontend**: HTMX + Tailwind CSS
- **Testing**: pytest
- **Type Checking**: basedpyright
- **Linting**: ruff