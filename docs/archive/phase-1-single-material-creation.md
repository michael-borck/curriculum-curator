# Phase 1: Single Material Creation (MVP)

> **Goal**: User can create ONE piece of instructional content from scratch with AI assistance  
> **Estimated Time**: 1-2 weeks  
> **Status**: Not Started

---

## Overview

This phase delivers the core value proposition: a user can log in, create a piece of content (lecture, worksheet, quiz), save it, and view it in their unit. This is the minimum viable product that proves the system works end-to-end.

---

## Task Breakdown

### 1.1 Fix Content Creator Page
**File**: `frontend/src/features/content/ContentCreator.tsx`

- [ ] **1.1.1** Add topic/prompt input field
  - Add text input for "Topic" (e.g., "Introduction to DNA Structure")
  - Add textarea for "Additional Context" (optional, e.g., "Focus on double helix, include diagrams")
  - Pass these to the generation endpoint

- [ ] **1.1.2** Fix LLM generation endpoint
  - Change from EventSource (broken) to regular POST request
  - Backend: Ensure `/api/llm/generate` accepts topic, pedagogy, content_type
  - Add proper streaming support OR simple request/response

- [ ] **1.1.3** Add loading states and error handling
  - Show spinner during generation
  - Toast notifications for errors
  - Retry button on failure

- [ ] **1.1.4** Connect pedagogy selection to generation
  - Ensure selected pedagogy (e.g., "constructivist") is passed to LLM
  - Update prompt templates to incorporate pedagogy

- [ ] **1.1.5** Save content correctly
  - POST to `/api/content` with unit_id, title, content, type
  - Handle validation errors
  - Show success message

- [ ] **1.1.6** Navigate after save
  - After successful save, navigate to content view page
  - OR navigate to unit view showing the new content

### 1.2 Create Content View Page
**New File**: `frontend/src/features/content/ContentView.tsx`

- [ ] **1.2.1** Create route `/units/:unitId/content/:contentId`
  - Add route to App.tsx
  - Create ContentView.tsx component

- [ ] **1.2.2** Fetch and display content
  - GET `/api/content/:contentId`
  - Display title, type, pedagogy, created date
  - Render content (HTML from rich text editor)

- [ ] **1.2.3** Add edit button
  - Navigate to ContentCreator with pre-filled data
  - OR inline editing mode

- [ ] **1.2.4** Add delete button
  - Confirmation modal
  - DELETE `/api/content/:contentId`
  - Navigate back to unit

- [ ] **1.2.5** Basic version indicator
  - Show "v1" or last modified date
  - Link to version history (Phase 2)

### 1.3 Update Unit View to Show Content
**File**: `frontend/src/features/units/UnitView.tsx` or `UnitWorkflow.tsx`

- [ ] **1.3.1** List content items
  - GET `/api/units/:unitId/content`
  - Display as cards or table
  - Show title, type, created date

- [ ] **1.3.2** Add content grouping (optional)
  - Group by module/week if assigned
  - OR show flat list for MVP

- [ ] **1.3.3** Quick actions per content
  - View button → ContentView
  - Edit button → ContentCreator (edit mode)
  - Delete button with confirmation

- [ ] **1.3.4** "Add Content" button
  - Prominent button on unit view
  - Navigate to ContentCreator with unit pre-selected

### 1.4 Backend Fixes
**Files**: `backend/app/api/routes/llm.py`, `backend/app/api/routes/content.py`

- [ ] **1.4.1** Fix `/api/llm/generate` endpoint
  - Accept POST with JSON body: `{topic, pedagogy, content_type, context}`
  - Return generated content as JSON
  - Handle streaming as optional

- [ ] **1.4.2** Verify `/api/content` CRUD
  - POST: Create content linked to unit
  - GET: List content by unit
  - GET /:id: Single content
  - PUT: Update content
  - DELETE: Remove content

- [ ] **1.4.3** Add content listing endpoint
  - GET `/api/units/:unitId/content`
  - Return all content for a unit
  - Include metadata (type, created, updated)

- [ ] **1.4.4** Fix any type errors
  - Address SQLAlchemy Column type issues
  - Ensure proper return types

---

## Acceptance Criteria

### User Story
> As a lecturer, I want to create a lecture with AI assistance so that I can quickly generate pedagogically-aligned content.

### Test Scenarios

1. **Create Content Flow**
   - [ ] User logs in and navigates to "Create Content"
   - [ ] User enters topic: "Introduction to Machine Learning"
   - [ ] User selects pedagogy: "Project-Based"
   - [ ] User selects content type: "Lecture"
   - [ ] User clicks "Generate"
   - [ ] AI generates content within 30 seconds
   - [ ] User sees content in rich text editor
   - [ ] User makes minor edits
   - [ ] User selects target unit
   - [ ] User clicks "Save"
   - [ ] Content appears in unit view

2. **View Content Flow**
   - [ ] User navigates to unit
   - [ ] User sees list of content items
   - [ ] User clicks on a content item
   - [ ] Content displays with full formatting
   - [ ] Edit and Delete buttons are visible

3. **Edit Content Flow**
   - [ ] User clicks Edit on content
   - [ ] Content loads in editor
   - [ ] User modifies content
   - [ ] User saves changes
   - [ ] Changes are reflected in view

4. **Delete Content Flow**
   - [ ] User clicks Delete on content
   - [ ] Confirmation modal appears
   - [ ] User confirms deletion
   - [ ] Content is removed from unit

---

## Technical Notes

### LLM Integration
The current ContentCreator uses EventSource which is broken. Options:
1. **Simple POST/Response**: Generate full content in one request (simplest)
2. **WebSocket Streaming**: Real-time streaming (better UX, more complex)
3. **Server-Sent Events**: Fix the EventSource approach (medium complexity)

**Recommendation**: Start with Simple POST/Response for MVP, add streaming later.

### Content Storage
Content should be stored as:
- Markdown (source of truth)
- HTML (for display, generated from Markdown)

The TipTap editor can handle both formats.

### API Endpoints Needed

```
POST /api/llm/generate
Body: { topic: string, pedagogy: string, content_type: string, context?: string }
Response: { content: string, metadata: { tokens_used: number, model: string } }

GET /api/units/:unitId/content
Response: [{ id, title, type, created_at, updated_at }]

POST /api/content
Body: { unit_id, title, content_markdown, content_type, pedagogy }
Response: { id, title, ... }

GET /api/content/:id
Response: { id, title, content_markdown, content_html, ... }

PUT /api/content/:id
Body: { title?, content_markdown?, ... }
Response: { id, ... }

DELETE /api/content/:id
Response: { success: true }
```

---

## Files to Create/Modify

### New Files
- `frontend/src/features/content/ContentView.tsx`
- `frontend/src/features/content/ContentList.tsx` (optional, could be in UnitView)

### Modified Files
- `frontend/src/features/content/ContentCreator.tsx` (major changes)
- `frontend/src/features/units/UnitView.tsx` (add content list)
- `frontend/src/App.tsx` (add routes)
- `backend/app/api/routes/llm.py` (fix generation)
- `backend/app/api/routes/content.py` (verify CRUD)
- `backend/app/services/llm_service.py` (ensure prompt templates work)

---

## Dependencies

- TipTap editor (already installed)
- LLM API keys configured in `.env`
- Database with Content model (already exists)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM API rate limits | Add queue/retry logic |
| Slow generation times | Add timeout, loading states |
| Content not saving | Add validation, error messages |
| Lost work on navigate | Auto-save draft locally |

---

## Definition of Done

- [ ] User can create content with AI assistance
- [ ] Content is saved to database
- [ ] Content appears in unit view
- [ ] Content can be viewed, edited, deleted
- [ ] No console errors in browser
- [ ] No server 500 errors
- [ ] Works on desktop Chrome/Firefox/Safari
- [ ] TypeScript compiles without errors
- [ ] Basic unit tests pass
