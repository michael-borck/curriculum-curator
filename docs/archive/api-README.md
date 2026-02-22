# API Documentation

Curriculum Curator provides several APIs for interacting with the system programmatically.

## API Categories

### [Core API](core.md)
Core functionality for course management, user authentication, and content generation.

### [Plugin APIs](plugins.md)
Interfaces for creating custom validators and remediators.

### [Web Routes](routes.md)
HTTP endpoints for the web application.

## Authentication

All API endpoints require authentication except for:
- `/login`
- `/signup`
- `/health`

Authentication is session-based with secure cookies.

## Response Format

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

## Common HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

API endpoints have the following rate limits:
- Authentication endpoints: 5 requests per minute
- Content generation: 10 requests per hour
- Other endpoints: 100 requests per minute

## API Versioning

The API is currently at version 1. Future versions will be accessible via:
- `/api/v1/` - Current version
- `/api/v2/` - Future version (when available)