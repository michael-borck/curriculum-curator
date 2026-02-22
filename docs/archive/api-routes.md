# Web Routes Reference

This document describes the web routes available in the Curriculum Curator application.

## Route Structure

All routes follow RESTful conventions where applicable:
- `GET` - Retrieve resources
- `POST` - Create new resources
- `PUT` - Update existing resources
- `DELETE` - Remove resources

## Authentication Routes

### Login Page
```
GET /login
```
Displays the login form.

### Login Action
```
POST /login
```
Processes login credentials.

**Form Data:**
- `email` - User email
- `password` - User password

**Response:**
- Success: Redirects to dashboard
- Failure: Returns to login with error message

### Logout
```
POST /logout
```
Logs out the current user and clears session.

### Signup Page
```
GET /signup
```
Displays the registration form.

### Signup Action
```
POST /signup
```
Creates a new user account.

**Form Data:**
- `email` - User email
- `password` - User password
- `full_name` - Full name
- `institution` - Institution name

## Main Application Routes

### Home/Dashboard
```
GET /
```
Displays the main dashboard with mode selection (Wizard/Expert).

### User Dashboard
```
GET /dashboard
```
Displays user's courses and recent activity.

## Wizard Mode Routes

### Wizard Start
```
GET /wizard
```
Starts the wizard mode workflow.

**Query Parameters:**
- `step` - Current step (1-5)

### Wizard Step 1: Topic & Audience
```
GET /wizard?step=1
```
Course topic and audience selection.

### Wizard Step 2: Course Structure
```
GET /wizard?step=2
```
Define weekly structure and topics.

### Wizard Step 3: Content Types
```
GET /wizard?step=3
```
Select material types for each week.

### Wizard Step 4: Review
```
GET /wizard?step=4
```
Review all selections before generation.

### Wizard Step 5: Generate
```
GET /wizard?step=5
```
Content generation and download.

### Wizard Form Submission
```
POST /wizard/submit
```
Processes wizard form data for each step.

**Form Data varies by step:**
- Step 1: `topic`, `audience`, `level`
- Step 2: `weeks`, `topics[]`
- Step 3: `materials[week][type]`
- Step 4: Confirmation
- Step 5: Generation options

## Expert Mode Routes

### Expert Mode Page
```
GET /expert
```
Displays the expert mode interface with all options.

### Expert Generate
```
POST /expert/generate
```
Generates content with expert settings.

**Form Data:**
- `course_title` - Course title
- `description` - Course description
- `weeks` - Number of weeks
- `materials` - Material configuration
- `teaching_style` - Override teaching style
- `advanced_options` - Additional options

## Course Management Routes

### List Courses
```
GET /courses
```
Displays all user's courses.

**Query Parameters:**
- `status` - Filter by status
- `sort` - Sort order
- `page` - Page number

### View Course
```
GET /courses/{course_id}
```
Displays course details and materials.

### Create Course
```
GET /courses/new
```
Displays course creation form.

```
POST /courses/create
```
Creates a new course.

### Edit Course
```
GET /courses/{course_id}/edit
```
Displays course editing form.

```
POST /courses/{course_id}/update
```
Updates course information.

### Delete Course
```
POST /courses/{course_id}/delete
```
Deletes a course (with confirmation).

### Archive Course
```
POST /courses/{course_id}/archive
```
Archives a course.

### Clone Course
```
POST /courses/{course_id}/clone
```
Creates a copy of the course.

## Material Routes

### View Material
```
GET /materials/{material_id}
```
Displays material content.

### Edit Material
```
GET /materials/{material_id}/edit
```
Displays material editor.

```
POST /materials/{material_id}/update
```
Saves material changes.

### Generate Material
```
POST /materials/{material_id}/generate
```
Generates or regenerates material content.

### Validate Material
```
POST /materials/{material_id}/validate
```
Runs validators on material.

### Export Material
```
GET /materials/{material_id}/export
```
Exports material in specified format.

**Query Parameters:**
- `format` - Export format (pdf, docx, html, markdown)

## Teaching Philosophy Routes

### Philosophy Questionnaire
```
GET /philosophy
```
Displays teaching philosophy questionnaire.

```
POST /philosophy/detect
```
Processes questionnaire and detects teaching style.

### Update Philosophy
```
POST /philosophy/update
```
Manually updates teaching philosophy.

## Settings Routes

### User Settings
```
GET /settings
```
Displays user settings page.

```
POST /settings/update
```
Updates user settings.

### Profile Settings
```
GET /settings/profile
```
Displays profile settings.

### Export Settings
```
GET /settings/export
```
Displays export preferences.

### Plugin Settings
```
GET /settings/plugins
```
Displays plugin configuration.

## API Endpoints

### Course API
```
GET /api/courses
POST /api/courses
GET /api/courses/{id}
PUT /api/courses/{id}
DELETE /api/courses/{id}
```

### Material API
```
GET /api/materials
POST /api/materials
GET /api/materials/{id}
PUT /api/materials/{id}
DELETE /api/materials/{id}
```

### Validation API
```
POST /api/validate
GET /api/validators
```

### Remediation API
```
POST /api/remediate
GET /api/remediators
```

## HTMX Endpoints

These endpoints return HTML fragments for HTMX updates:

### Dynamic Form Fields
```
GET /htmx/course-weeks
```
Returns week input fields based on number.

**Query Parameters:**
- `count` - Number of weeks

### Material Type Selector
```
GET /htmx/material-types
```
Returns material type checkboxes.

**Query Parameters:**
- `week` - Week number

### Progress Updates
```
GET /htmx/generation-progress
```
Returns generation progress bar.

**Query Parameters:**
- `job_id` - Generation job ID

### Validation Results
```
GET /htmx/validation-results
```
Returns formatted validation results.

**Query Parameters:**
- `material_id` - Material to validate

## Static Routes

### Static Files
```
GET /static/{file}
```
Serves static CSS, JS, and image files.

### Uploaded Files
```
GET /uploads/{file}
```
Serves user-uploaded files (authenticated).

### Export Downloads
```
GET /downloads/{file}
```
Serves generated export files (authenticated).

## Utility Routes

### Health Check
```
GET /health
```
Returns application health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Feature Flags
```
GET /features
```
Returns enabled features for the current user.

## WebSocket Routes (Future)

### Generation Updates
```
WS /ws/generation/{job_id}
```
Real-time generation progress updates.

### Collaboration
```
WS /ws/course/{course_id}/collaborate
```
Real-time collaboration features.

## Route Parameters

### Common Parameters

- `{course_id}` - UUID of the course
- `{material_id}` - UUID of the material
- `{user_id}` - UUID of the user
- `{job_id}` - UUID of async job

### Query Parameter Patterns

- Pagination: `?page=1&per_page=20`
- Sorting: `?sort=created&order=desc`
- Filtering: `?status=active&type=lecture`
- Search: `?q=python+functions`

## Response Types

### HTML Responses
Most routes return full HTML pages or fragments (for HTMX).

### JSON Responses
API routes (`/api/*`) return JSON.

### File Downloads
Export routes return files with appropriate headers.

## Error Handling

### 404 Not Found
```
GET /404
```
Custom 404 error page.

### 500 Server Error
```
GET /500
```
Custom error page for server errors.

### Validation Errors
Form validation errors are displayed inline using HTMX.

## Security

### CSRF Protection
All POST routes require CSRF tokens.

### Authentication Required
Most routes require authentication except:
- `/login`
- `/signup`
- `/health`
- `/static/*`

### Rate Limiting
- Login attempts: 5 per minute
- API calls: 100 per minute
- Generation: 10 per hour

## Examples

### Creating a Course (Wizard Mode)
```
1. GET /wizard?step=1
2. POST /wizard/submit (step=1)
3. GET /wizard?step=2
4. POST /wizard/submit (step=2)
5. GET /wizard?step=3
6. POST /wizard/submit (step=3)
7. GET /wizard?step=4
8. POST /wizard/submit (step=4)
9. GET /wizard?step=5
10. Course created and materials generated
```

### Quick Material Generation (Expert Mode)
```
1. GET /expert
2. Fill out comprehensive form
3. POST /expert/generate
4. Receive generated materials immediately
```

### Editing Existing Material
```
1. GET /courses/{course_id}
2. Click on material
3. GET /materials/{material_id}/edit
4. Make changes
5. POST /materials/{material_id}/update
6. Optional: POST /materials/{material_id}/validate
```