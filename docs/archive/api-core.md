# Core API Reference

The Core API provides programmatic access to Curriculum Curator's main functionality.

## Authentication

### Login
```http
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "teaching_philosophy": "constructivist"
  }
}
```

### Logout
```http
POST /api/logout
```

### Get Current User
```http
GET /api/user
```

## User Management

### Create User
```http
POST /api/users
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "institution": "University Name"
}
```

### Update User Profile
```http
PUT /api/users/{user_id}
Content-Type: application/json

{
  "full_name": "Jane Doe",
  "institution": "New University",
  "teaching_philosophy": "flipped_classroom"
}
```

### Update Teaching Philosophy
```http
POST /api/users/{user_id}/teaching-philosophy
Content-Type: application/json

{
  "philosophy": "constructivist",
  "custom_indicators": {
    "interaction_level": 8,
    "structure_preference": 5,
    "student_centered": 9,
    "technology_integration": 7,
    "assessment_frequency": "high",
    "collaboration_emphasis": 8
  }
}
```

## Course Management

### List Courses
```http
GET /api/courses
```

**Query Parameters:**
- `status` - Filter by status (active, archived, draft)
- `sort` - Sort by field (created, updated, title)
- `limit` - Number of results (default: 20)
- `offset` - Pagination offset

**Response:**
```json
{
  "status": "success",
  "data": {
    "courses": [
      {
        "id": "course-uuid",
        "title": "Introduction to Python",
        "description": "Learn Python basics",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z",
        "weeks": 12,
        "materials_count": 36
      }
    ],
    "total": 5,
    "limit": 20,
    "offset": 0
  }
}
```

### Create Course
```http
POST /api/courses
Content-Type: application/json

{
  "title": "Advanced Python Programming",
  "description": "Deep dive into Python",
  "institution": "Tech University",
  "department": "Computer Science",
  "course_code": "CS301",
  "credits": 3,
  "level": "undergraduate",
  "duration_weeks": 15,
  "hours_per_week": 3,
  "delivery_mode": "hybrid",
  "max_students": 30,
  "prerequisites": ["CS101", "CS201"],
  "learning_outcomes": [
    "Master advanced Python concepts",
    "Build complex applications",
    "Understand design patterns"
  ],
  "teaching_philosophy_override": "project_based"
}
```

### Get Course Details
```http
GET /api/courses/{course_id}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "course-uuid",
    "title": "Advanced Python Programming",
    "description": "Deep dive into Python",
    "metadata": {
      "institution": "Tech University",
      "department": "Computer Science",
      "course_code": "CS301",
      "credits": 3,
      "level": "undergraduate"
    },
    "structure": {
      "duration_weeks": 15,
      "hours_per_week": 3,
      "delivery_mode": "hybrid",
      "max_students": 30
    },
    "content": {
      "prerequisites": ["CS101", "CS201"],
      "learning_outcomes": [
        "Master advanced Python concepts",
        "Build complex applications",
        "Understand design patterns"
      ]
    },
    "settings": {
      "teaching_philosophy": "project_based",
      "auto_generate": true,
      "validation_enabled": true
    },
    "weeks": [
      {
        "week_number": 1,
        "topic": "Advanced Functions and Decorators",
        "materials": [
          {
            "id": "material-uuid",
            "type": "lecture",
            "title": "Understanding Decorators",
            "status": "generated"
          }
        ]
      }
    ]
  }
}
```

### Update Course
```http
PUT /api/courses/{course_id}
Content-Type: application/json

{
  "title": "Updated Course Title",
  "description": "Updated description",
  "status": "active"
}
```

### Delete Course
```http
DELETE /api/courses/{course_id}
```

### Archive Course
```http
POST /api/courses/{course_id}/archive
```

### Clone Course
```http
POST /api/courses/{course_id}/clone
Content-Type: application/json

{
  "title": "Cloned Course Title",
  "include_materials": true
}
```

## Material Management

### List Course Materials
```http
GET /api/courses/{course_id}/materials
```

**Query Parameters:**
- `week` - Filter by week number
- `type` - Filter by type (lecture, worksheet, quiz, etc.)
- `status` - Filter by status (draft, generated, reviewed, published)

### Create Material
```http
POST /api/courses/{course_id}/materials
Content-Type: application/json

{
  "week_number": 1,
  "type": "lecture",
  "title": "Introduction to Functions",
  "topic": "Functions and Parameters",
  "duration_minutes": 50,
  "learning_objectives": [
    "Define functions",
    "Use parameters",
    "Return values"
  ],
  "prerequisites": ["Basic Python syntax"],
  "teaching_notes": "Start with simple examples"
}
```

### Get Material
```http
GET /api/materials/{material_id}
```

### Update Material
```http
PUT /api/materials/{material_id}
Content-Type: application/json

{
  "content": "# Updated Lecture Content\n\n...",
  "status": "reviewed"
}
```

### Delete Material
```http
DELETE /api/materials/{material_id}
```

## Content Generation

### Generate Material Content
```http
POST /api/materials/{material_id}/generate
Content-Type: application/json

{
  "regenerate": false,
  "style_override": null,
  "additional_context": {
    "emphasis": "practical examples",
    "avoid_topics": ["complex math"]
  },
  "llm_provider": "openai",
  "llm_model": "gpt-4"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "material_id": "material-uuid",
    "content": "# Introduction to Functions\n\n...",
    "generation_metadata": {
      "provider": "openai",
      "model": "gpt-4",
      "tokens_used": 1500,
      "generation_time_ms": 3200,
      "teaching_style": "constructivist"
    }
  }
}
```

### Generate Multiple Materials (Batch)
```http
POST /api/courses/{course_id}/generate-materials
Content-Type: application/json

{
  "material_ids": ["id1", "id2", "id3"],
  "parallel": true,
  "validation_enabled": true,
  "auto_remediate": true
}
```

**Response (Streaming):**
```json
{"type": "progress", "material_id": "id1", "status": "generating"}
{"type": "progress", "material_id": "id1", "status": "validating"}
{"type": "complete", "material_id": "id1", "success": true}
{"type": "progress", "material_id": "id2", "status": "generating"}
...
```

## Validation

### Validate Content
```http
POST /api/validate
Content-Type: application/json

{
  "content": "Content to validate...",
  "validators": ["readability", "structure", "grammar"],
  "context": {
    "material_type": "lecture",
    "grade_level": "undergraduate",
    "subject": "computer science"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "overall_score": 85,
    "validators": {
      "readability": {
        "score": 90,
        "issues": [
          {
            "type": "long_sentence",
            "severity": "info",
            "message": "Sentence is longer than 25 words",
            "line": 5,
            "suggestion": "Consider breaking into two sentences"
          }
        ]
      },
      "structure": {
        "score": 85,
        "issues": []
      },
      "grammar": {
        "score": 80,
        "issues": [
          {
            "type": "passive_voice",
            "severity": "info",
            "message": "Passive voice detected",
            "line": 12
          }
        ]
      }
    }
  }
}
```

### Get Available Validators
```http
GET /api/validators
```

### Get Validator Details
```http
GET /api/validators/{validator_name}
```

## Remediation

### Remediate Content
```http
POST /api/remediate
Content-Type: application/json

{
  "content": "Content to remediate...",
  "issues": [
    {
      "type": "long_sentence",
      "severity": "warning",
      "line": 5
    }
  ],
  "remediators": ["sentence_splitter", "format_corrector"],
  "auto_select": true
}
```

### Get Available Remediators
```http
GET /api/remediators
```

## Export

### Export Material
```http
POST /api/materials/{material_id}/export
Content-Type: application/json

{
  "format": "pdf",
  "include_metadata": true,
  "include_teaching_notes": false,
  "template": "academic"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "download_url": "/downloads/export-uuid.pdf",
    "expires_at": "2024-01-02T00:00:00Z"
  }
}
```

### Export Course
```http
POST /api/courses/{course_id}/export
Content-Type: application/json

{
  "format": "zip",
  "include_all_weeks": true,
  "material_formats": ["markdown", "pdf"],
  "structure": "hierarchical"
}
```

### Supported Export Formats
- `markdown` - Markdown files
- `html` - HTML files
- `pdf` - PDF documents
- `docx` - Microsoft Word
- `latex` - LaTeX source
- `zip` - Archive of multiple formats

## Search

### Search Courses
```http
GET /api/search/courses?q=python&limit=10
```

### Search Materials
```http
GET /api/search/materials?q=functions&course_id=uuid&type=lecture
```

## Settings

### Get User Settings
```http
GET /api/settings
```

### Update Settings
```http
PUT /api/settings
Content-Type: application/json

{
  "default_teaching_philosophy": "constructivist",
  "auto_validate": true,
  "default_validators": ["readability", "structure"],
  "export_preferences": {
    "default_format": "pdf",
    "include_metadata": true
  },
  "llm_preferences": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

## Webhooks

### Register Webhook
```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://example.com/webhook",
  "events": ["material.generated", "course.published"],
  "secret": "webhook-secret"
}
```

### Webhook Events
- `course.created`
- `course.updated`
- `course.deleted`
- `course.published`
- `material.created`
- `material.generated`
- `material.validated`
- `material.published`
- `generation.started`
- `generation.completed`
- `generation.failed`

### Webhook Payload Example
```json
{
  "event": "material.generated",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "material_id": "uuid",
    "course_id": "uuid",
    "type": "lecture",
    "title": "Introduction to Functions"
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "status": "error",
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "title",
    "message": "Title is required"
  }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED` - User not authenticated
- `PERMISSION_DENIED` - User lacks permission
- `RESOURCE_NOT_FOUND` - Resource doesn't exist
- `VALIDATION_ERROR` - Input validation failed
- `GENERATION_FAILED` - Content generation failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

## Rate Limiting

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination:
```http
GET /api/courses?limit=20&offset=40
```

Response includes pagination metadata:
```json
{
  "data": { ... },
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 40,
    "has_next": true,
    "has_prev": true
  }
}
```