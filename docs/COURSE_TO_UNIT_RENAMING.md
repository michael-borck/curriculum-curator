# Course to Unit Renaming Plan

## Models to Rename
1. `CourseOutline` → `UnitOutline`
2. `CourseStructureStatus` → `UnitStructureStatus`

## Database Tables to Rename
1. `course_outlines` → `unit_outlines`

## Files to Rename
### Backend Models
- `/backend/app/models/course_outline.py` → `unit_outline.py`

### Backend Schemas
- `/backend/app/schemas/course.py` → `unit.py`
- `/backend/app/schemas/course_structure.py` → `unit_structure.py`
- `/backend/app/schemas/course_module.py` → (remove - not used)

### Backend Routes
- `/backend/app/api/routes/course_structure.py` → `unit_structure.py`
- `/backend/app/api/routes/course_modules.py` → (already disabled)
- `/backend/app/api/routes/courses.py` → Keep name for API compatibility

### Frontend Components
- Check for CourseStructure components → rename to UnitStructure

## Foreign Key References to Update
All models that have `course_outline_id`:
- AssessmentPlan
- WorkflowChatSession
- WeeklyTopic
- UnitLearningOutcome

## API Endpoints
Keep `/api/courses` for now for compatibility, but internally everything uses Unit models.

## Migration Required
Since we have a `course_outlines` table with foreign keys, we need to:
1. Create new `unit_outlines` table
2. Copy data from `course_outlines` to `unit_outlines`
3. Update foreign keys
4. Drop old table

OR since we're in development:
1. Just drop and recreate the database with correct names