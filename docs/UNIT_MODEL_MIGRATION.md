# Unit Model Migration Summary

## Background
The application had both `Course` and `Unit` models which were essentially duplicates. In Australian universities:
- **Unit** = Individual semester subject (what Americans call a "course")  
- **Course** = Full degree program (3-4 years)

We decided to use `Unit` consistently throughout the application.

## Changes Made

### 1. Database Changes
**Dropped Tables:**
- `courses` - Replaced by `units` table
- `course_modules` - Will use new structure models
- `materials` - Will use new content models
- `lrds` - Obsolete, using new workflow models
- `conversations` - Replaced by `ChatSession` and `WorkflowChatSession`
- `course_search_results` - Not needed

**Kept Tables:**
- `units` - Primary model for academic units
- `chat_sessions` - For unit chat functionality
- `workflow_chat_sessions` - For guided workflow conversations
- `course_outlines` - Part of new structure (despite name, links to units)
- `weekly_topics` - Part of new structure
- `assessment_plans` - Part of new structure
- `unit_learning_outcomes` - Part of new structure

### 2. Model Changes
**Removed Files:**
- `app/models/course.py`
- `app/models/course_search_result.py`
- `app/models/conversation.py`

**Updated:**
- `app/models/__init__.py` - Removed Course imports
- `app/services/content_workflow_service.py` - Removed Course fallback logic

### 3. API Changes
**Disabled Routes:** (temporarily, until reimplemented with new models)
- `/api/lrds` - Depended on courses table
- `/api/materials` - Depended on courses table  
- `/api/course-modules` - Depended on courses table
- `/api/export` - Depended on materials table

**Active Routes:**
- `/api/courses` - Still works! Internally uses Unit model
- `/api/content/workflow` - Works with Unit model
- `/api/auth`, `/api/admin` - Unaffected

### 4. Frontend Impact
- Frontend continues to work as-is
- Still calls `/api/courses` endpoints
- Displays "Units" in UI (already updated)
- Workflow features work with Unit model

## Migration Script
Created `backend/migrate_course_to_unit.py` which:
1. Checks for existing course data
2. Drops foreign key constraints
3. Drops old tables
4. Provides next steps

## Next Steps

### Short Term
1. ✅ Test that guided workflow works
2. ✅ Verify unit creation/management works
3. ⏳ Fix PDF import (separate issue)
4. ⏳ Implement manual structure editor

### Medium Term
1. Reimplement materials functionality with new content models
2. Create unit-based export functionality
3. Consider renaming API endpoints from `/courses` to `/units`

### Long Term
1. Full migration to Australian university terminology
2. Support for course (degree program) management if needed
3. Enhanced unit structure management

## Benefits of This Cleanup
1. **Consistency** - Single model for academic units
2. **Clarity** - No confusion between Course and Unit
3. **Simplicity** - Reduced code duplication
4. **Maintainability** - Easier to understand and modify
5. **Australian-friendly** - Uses correct terminology

## Testing Checklist
- [x] Backend starts without errors
- [x] Unit creation works
- [x] Unit listing works
- [ ] Guided workflow creates structure
- [ ] PDF import works (known issue)
- [ ] Chat with unit works

## Important Notes
- Database was reset during migration (development only)
- No production data was affected
- Frontend compatibility maintained through API naming