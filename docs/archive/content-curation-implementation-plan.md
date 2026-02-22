# Content Curation Implementation Plan

> **Status**: Active Development  
> **Created**: 2025-11-28  
> **Last Updated**: 2025-11-28

---

## Executive Summary

This plan addresses the core gap in Curriculum Curator: **users cannot create instructional materials**. The system has database models and UI scaffolding, but no cohesive workflow for content creation, import, or curation.

---

## Current State Analysis

### What Works
- [x] User registration and login
- [x] Basic unit CRUD (create, list, delete)
- [x] Landing page with feature descriptions
- [x] Dashboard layout with navigation
- [x] Database models exist (Unit, Module, Content, LearningOutcome, Assessment)
- [x] LLM service with multi-provider support
- [x] Rich text editor component (TipTap-based)
- [x] Admin dashboard structure (partially functional)

### What's Broken or Missing
- [ ] **Admin Dashboard**: Renders but API calls fail (routes exist but return errors)
- [ ] **Content Creation**: ContentCreator.tsx exists but:
  - Generate button uses broken EventSource endpoint
  - No topic/prompt input for generation
  - Save function creates content but nowhere to view it
- [ ] **Unit Workflow**: UnitWorkflow.tsx shows 3 options but:
  - "Guided Creation" wizard doesn't fully work
  - PDF Import dialog exists but backend processing incomplete
  - "Manual Creation" just navigates to empty structure page
- [ ] **Import Materials**: ImportMaterials.tsx has UI but:
  - Upload endpoint exists, processing returns basic analysis
  - No actual content extraction/creation from uploaded files
- [ ] **Unit Structure View**: UnitStructure.tsx is empty/minimal
- [ ] **Teaching Style**: TeachingStyle.tsx exists but not integrated into generation
- [ ] **Validators/Remediators**: Plugin architecture exists but no implementations

### Current User Journey (Broken)
```
1. User logs in
2. Sees "My Units" page (UnitManager) - WORKS
3. Creates a unit with metadata - WORKS
4. Clicks on unit → UnitWorkflow page
5. Sees 3 options: Guided, Import, Manual
6. All 3 options lead to dead ends or errors
7. User cannot create any actual content
```

---

## Desired User Journey

### Journey 1: Quick Single Material Creation
```
1. User logs in → Dashboard
2. Clicks "Create Content" in sidebar OR "+" on any unit
3. Selects content type (Lecture, Worksheet, Quiz, etc.)
4. Optionally selects/creates a unit to attach to
5. Enters topic + optional context
6. Selects teaching philosophy (or uses default)
7. Clicks "Generate" → AI creates draft
8. User edits in rich text editor
9. Runs validators (readability, structure)
10. Saves content → visible in unit structure
```

### Journey 2: Import & Enhance Existing Material
```
1. User has existing PDF/DOCX syllabus or lecture
2. Goes to Import page
3. Uploads file
4. System extracts text, detects structure
5. User reviews extracted content
6. AI suggests improvements
7. User applies fixes or manually edits
8. Saves enhanced content
```

### Journey 3: Build Full Unit Structure
```
1. User creates unit with title/description
2. Chooses "Generate 12-Week Schedule"
3. AI proposes weekly topics
4. User adjusts/accepts schedule
5. For each week, user can:
   - Generate lectures/materials
   - Import existing content
   - Manually create content
6. Defines Learning Outcomes (ULOs)
7. Creates assessments with weightings
8. System validates alignment
```

---

## Implementation Phases

## Phase 1: Single Material Creation (MVP) ⬅️ START HERE
**Goal**: User can create ONE piece of content from scratch with AI assistance

### 1.1 Fix Content Creator Page
- [ ] Add topic/prompt input field
- [ ] Fix LLM generation endpoint (POST not EventSource)
- [ ] Add loading states and error handling
- [ ] Make pedagogy selection actually influence generation
- [ ] Save content to database correctly
- [ ] Navigate to view content after save

### 1.2 Create Content View Page
- [ ] New page: `/units/:unitId/content/:contentId`
- [ ] Display saved content with metadata
- [ ] Edit button → back to editor
- [ ] Delete button with confirmation
- [ ] Version history (basic)

### 1.3 Update Unit View to Show Content
- [ ] List all content items in a unit
- [ ] Group by week/module if applicable
- [ ] Quick actions: view, edit, delete
- [ ] "Add Content" button per week

### 1.4 Backend Fixes
- [ ] Fix `/api/llm/generate` endpoint
- [ ] Ensure `/api/content` CRUD works
- [ ] Add content listing by unit endpoint

**Deliverable**: User can create a lecture, save it, and see it in their unit.

---

## Phase 2: Week/Module Structure
**Goal**: User can organize content into weeks within a unit

### 2.1 Module/Week Management
- [ ] Create Module model UI (already in DB)
- [ ] Add/edit/delete weeks in a unit
- [ ] Drag-drop reorder weeks
- [ ] Assign content to weeks

### 2.2 Unit Structure View
- [ ] Tabbed interface: Structure | Outcomes | Assessments
- [ ] Visual week-by-week breakdown
- [ ] Content count per week
- [ ] Progress indicators

### 2.3 Quick Add from Structure
- [ ] "+" button on each week
- [ ] Modal to create content for that week
- [ ] Pre-filled week context

**Deliverable**: User can structure a unit into weeks and add content to each.

---

## Phase 3: Import Capabilities
**Goal**: User can import existing materials and enhance them

### 3.1 PDF/DOCX Text Extraction
- [ ] Backend: Extract text from uploaded files
- [ ] Frontend: Show extracted text preview
- [ ] Allow manual correction of extraction

### 3.2 Structure Detection
- [ ] Detect headings, sections, lists
- [ ] Propose content type based on content
- [ ] Allow user override

### 3.3 Enhancement Suggestions
- [ ] Run basic validators on imported content
- [ ] Show readability score
- [ ] AI suggestions for improvement
- [ ] One-click "Apply All Fixes"

### 3.4 Import to Unit
- [ ] Choose target unit and week
- [ ] Create content record from import
- [ ] Track original source file

**Deliverable**: User can upload a PDF lecture, extract content, enhance it, and save to unit.

---

## Phase 4: AI Schedule Generation
**Goal**: Generate full 12-week unit structure from description

### 4.1 Schedule Generator
- [ ] Input: Unit title, description, learning goals
- [ ] AI generates 12-week topic schedule
- [ ] JSON structure with week titles/descriptions
- [ ] Preview before applying

### 4.2 Apply Schedule
- [ ] Create Module records for each week
- [ ] Pre-populate week descriptions
- [ ] Show empty content placeholders

### 4.3 Bulk Content Generation
- [ ] "Generate All Lectures" button
- [ ] Queue-based generation
- [ ] Progress indicator
- [ ] Review each before saving

**Deliverable**: User enters unit description, gets complete 12-week structure with AI-generated content.

---

## Phase 5: Validators & Remediation
**Goal**: Quality assurance for all content

### 5.1 Implement Core Validators
- [ ] Readability validator (Flesch-Kincaid)
- [ ] Structure validator (headings, sections)
- [ ] Australian English validator
- [ ] Learning objective alignment validator

### 5.2 Validator UI
- [ ] "Check Content" button
- [ ] Visual results panel
- [ ] Pass/fail indicators
- [ ] Issue details with line numbers

### 5.3 Auto-Fix (Remediation)
- [ ] "Fix All Issues" button
- [ ] AI rewrites problem sections
- [ ] Preview changes before apply
- [ ] Undo capability

**Deliverable**: User runs validators on content, sees issues, clicks "Fix" and content improves.

---

## Phase 6: Learning Outcomes & Assessments
**Goal**: Full curriculum alignment features

### 6.1 ULO Management
- [ ] Create/edit Learning Outcomes
- [ ] Bloom's Taxonomy level selector
- [ ] Drag-drop reorder

### 6.2 Assessment Management
- [ ] Create assessments with weights
- [ ] Link to ULOs
- [ ] Weight validation (must = 100%)

### 6.3 Alignment Dashboard
- [ ] Visual ULO coverage map
- [ ] Formative vs Summative split
- [ ] Missing coverage warnings

**Deliverable**: User defines ULOs, creates assessments, sees alignment visualization.

---

## Technical Tasks (Cross-Phase)

### Frontend
- [ ] Fix TypeScript `any` types in UnitManager.tsx
- [ ] Add proper error boundaries
- [ ] Implement loading skeletons
- [ ] Add toast notifications for all actions
- [ ] Mobile responsive fixes

### Backend
- [ ] Fix Admin dashboard API routes
- [ ] Implement content versioning
- [ ] Add audit logging
- [ ] Fix deprecated `datetime.utcnow()` usage
- [ ] Remove debug middleware from production

### Testing
- [ ] Add unit tests for content creation
- [ ] Add integration tests for full workflows
- [ ] Fix existing test-implementation mismatches

---

## UI/UX Issues Found

### Landing Page (Landing.tsx)
- ✅ Looks good, clear value proposition
- ⚠️ "Watch Demo" button does nothing

### Login (Login.tsx)
- ✅ Basic login works
- ⚠️ No "Forgot Password" visible (exists at /password-reset)
- ⚠️ No registration link visible

### Dashboard Layout (Dashboard.tsx)
- ✅ Clean sidebar navigation
- ⚠️ Search bar doesn't work (no implementation)
- ⚠️ Notification bell is decorative only

### Unit Manager (UnitManager.tsx)
- ✅ Unit creation works
- ✅ Unit list displays correctly
- ⚠️ Edit button does nothing (TODO comment in code)
- ⚠️ Credit points validation mismatch (schema says 100 max, but UnitUpdate says 12 max)

### Unit Workflow (UnitWorkflow.tsx)
- ✅ Good 3-option layout for new users
- ❌ "Guided Creation" wizard incomplete
- ❌ "PDF Import" dialog exists but backend broken
- ⚠️ "Manual Creation" goes to empty structure page

### Content Creator (ContentCreator.tsx)
- ✅ Good layout with editor + sidebar
- ❌ Generate button uses broken EventSource
- ❌ No topic input - can't tell AI what to generate
- ⚠️ Pedagogy selector works but not connected to generation
- ⚠️ Export buttons do nothing

### Import Materials (ImportMaterials.tsx)
- ✅ Good drag-drop UI
- ✅ File upload works
- ⚠️ Backend analysis returns minimal data
- ❌ "Enhance with AI" and "Edit Content" navigate to non-existent pages

### Admin Dashboard (features/admin/AdminDashboard.tsx)
- ✅ Proper layout with sidebar
- ✅ User management UI exists
- ❌ API calls fail (500 errors or missing endpoints)
- ⚠️ Email whitelist UI exists but may not be connected

---

## Priority Order

1. **Phase 1**: Single material creation (1-2 weeks)
   - Biggest bang for buck
   - Enables testing of full flow
   - Foundation for everything else

2. **Phase 2**: Week structure (1 week)
   - Natural extension of Phase 1
   - Needed for proper unit organization

3. **Phase 3**: Import (1-2 weeks)
   - High value for users with existing content
   - PDF extraction is complex

4. **Phase 4**: Schedule generation (1 week)
   - Impressive demo feature
   - Builds on Phases 1-2

5. **Phase 5**: Validators (1-2 weeks)
   - Quality assurance
   - Differentiating feature

6. **Phase 6**: Alignment (1-2 weeks)
   - Full curriculum design
   - Professional feature

---

## Next Steps

1. [ ] Review this plan and confirm priorities
2. [ ] Start Phase 1.1: Fix Content Creator Page
3. [ ] Create GitHub issues for tracking

---

## Notes

- This is a greenfield project - no production users
- OK to break backwards compatibility
- OK to reset database as needed
- Focus on getting a working flow first, polish later
