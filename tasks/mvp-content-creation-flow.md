# MVP Task List: Content Creation Flow

**Goal**: User can log in, create a piece of content (lecture, worksheet, quiz), save it, and view it in their unit.

**Status**: Phase 1 & 2 Complete - Ready for Testing  
**Created**: 2025-12-01  
**Updated**: 2025-12-01  
**Related ADRs**: [ADR-015](../docs/adr/015-content-format-and-export-strategy.md), [ADR-016](../docs/adr/016-react-typescript-frontend.md), [ADR-017](../docs/adr/017-fastapi-rest-backend.md)

---

## Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Authentication | ✅ Working | Login, register, JWT auth |
| Unit Management | ✅ Working | Create, view, delete units |
| LLM Generation | ✅ Working | Multi-provider, streaming |
| TipTap Editor | ✅ Working | Rich text editing |
| Content Save | ✅ Fixed | API path and field names corrected |
| Content View | ✅ Fixed | API integration complete |
| Content Edit | ✅ Fixed | Edit mode in ContentCreator |
| Content Export | ⏳ Planned | Per ADR-015 (Quarto) |

---

## Phase 1: Fix Critical Bugs (MVP Blocker) ✅ COMPLETE

### 1.1 Fix Content API Path ✅
- [x] **Frontend**: Update `createContent` in `frontend/src/services/api.ts`
  - Changed from `/content` to `/units/${unitId}/content`
  - Added `unitId` parameter to function signature
- [x] **Frontend**: Update `ContentCreator.tsx` to pass `unitId` to API call

### 1.2 Fix Field Name Mismatch ✅
- [x] **Frontend**: Update `ContentCreator.tsx` request payload
  - Changed `content_markdown` → `body`
  - Changed `type` → `contentType` (match schema)
  - Removed redundant `unit_id` from body (it's in URL path)

### 1.3 Add Content API Functions ✅
- [x] **Frontend**: Add `getUnitContents(unitId)` function to `api.ts`
- [x] **Frontend**: Add `getContent(unitId, contentId)` function
- [x] **Frontend**: Add `updateContent(unitId, contentId, data)` function
- [x] **Frontend**: Add `deleteContent(unitId, contentId)` function

---

## Phase 2: Content View Integration ✅ COMPLETE

### 2.1 Unit Dashboard Content List ✅
- [x] **Frontend**: Content list already exists in `UnitView.tsx`
- [x] **Frontend**: Display content cards (title, type, updated date)
- [x] **Frontend**: "Add Content" button links to ContentCreator
- [x] **Frontend**: Fixed API call to use `getUnitContents`

### 2.2 Content View Page ✅
- [x] **Frontend**: Route `/units/:unitId/content/:contentId` exists
- [x] **Frontend**: `ContentView.tsx` updated with:
  - Fixed API calls to include unitId
  - Correct field names (`body`, `contentType`)
  - Edit button (links to editor)
  - Delete button with confirmation

### 2.3 Content Edit Mode ✅
- [x] **Frontend**: ContentCreator supports edit mode via URL params
- [x] **Frontend**: Pre-populates fields with existing content
- [x] **Frontend**: Uses `updateContent` instead of `createContent` when editing
- [x] **Frontend**: Unit selector disabled in edit mode

---

## Phase 3: TipTap Markdown Integration (Per ADR-015)

### 3.1 Add tiptap-markdown Extension
- [ ] **Frontend**: Install `tiptap-markdown` package
- [ ] **Frontend**: Configure TipTap to use markdown storage
- [ ] **Frontend**: Update `RichTextEditor.tsx` to output markdown
- [ ] **Test**: Verify round-trip (markdown → TipTap → markdown)

### 3.2 Backend Markdown Storage
- [x] **Verify**: Backend Content model stores markdown in `body` field
- [x] **Verify**: Git content service handles markdown files

---

## Phase 4: Export Functionality (Per ADR-015)

### 4.1 Install Quarto Backend
- [ ] **Backend**: Add Quarto dependency to Docker/deployment
- [ ] **Backend**: Create `QuartoService` for rendering
- [ ] **Backend**: Add `/api/units/{unit_id}/content/{content_id}/export` endpoint
- [ ] **Backend**: Support formats: `html`, `pdf`, `docx`, `pptx`

### 4.2 Export UI
- [ ] **Frontend**: Add export dropdown to ContentView
- [ ] **Frontend**: Options: Copy HTML, Download PDF, Download DOCX
- [ ] **Frontend**: For slides content type: Add PPTX option

### 4.3 Copy to Clipboard (LMS Integration)
- [ ] **Frontend**: Add "Copy for LMS" button
- [ ] **Frontend**: Copy rendered HTML with inline styles
- [ ] **Frontend**: Show success toast notification

---

## Phase 5: Content Types

### 5.1 Worksheet Content Type
- [ ] **Verify**: Worksheet renders correctly in TipTap
- [ ] **Verify**: PDF export includes proper formatting

### 5.2 Quiz Content Type
- [ ] **Frontend**: Add quiz-specific structure (questions, answers)
- [ ] **Frontend**: Preview mode for quiz testing
- [ ] **Backend**: Quiz content schema

### 5.3 Slides Content Type
- [ ] **Frontend**: Slide-aware editing (H1 = new slide)
- [ ] **Frontend**: Slide preview panel
- [ ] **Backend**: PPTX export via Quarto

---

## Phase 6: Polish & UX

### 6.1 Auto-save
- [ ] **Frontend**: Debounced auto-save while editing
- [ ] **Frontend**: Save indicator ("Saving...", "Saved")

### 6.2 Loading States
- [x] **Frontend**: Spinner during LLM generation (exists)
- [x] **Frontend**: Loading state for content fetch (added)
- [ ] **Frontend**: Skeleton loaders for content list
- [ ] **Frontend**: Progress indicator for exports

### 6.3 Error Handling
- [x] **Frontend**: Toast messages for API failures (exists)
- [ ] **Frontend**: Retry button for failed operations

---

## Testing Checklist

### End-to-End Flow (Ready to Test)
- [ ] Login with valid credentials
- [ ] Navigate to Units page
- [ ] Create a new unit (or select existing)
- [ ] Click "Add Content" from unit view
- [ ] Enter topic, select pedagogy
- [ ] Click "Generate" to create with AI
- [ ] Edit content in TipTap editor
- [ ] Click "Save"
- [ ] Navigate back to unit dashboard
- [ ] See saved content in list
- [ ] Click content to view
- [ ] Click "Edit" to modify
- [ ] Save changes

### Edge Cases
- [ ] Save without title (should error)
- [ ] Save empty content (should warn)
- [ ] Handle LLM API timeout
- [ ] Handle network disconnection

---

## Files Modified

```
frontend/src/services/api.ts
  - Fixed content API paths (nested under /units/{unitId}/content)
  - Updated function signatures to require unitId
  - Added getUnitContents, getContent, updateContent, deleteContent

frontend/src/types/index.ts
  - Updated Content interface to match API response
  - Changed contentMarkdown → body
  - Changed type → contentType

frontend/src/features/content/ContentCreator.tsx
  - Added edit mode support (loads existing content)
  - Fixed API call to use correct path and field names
  - Uses updateContent when editing, createContent when new

frontend/src/features/content/ContentView.tsx
  - Fixed API calls to include unitId
  - Updated field references (body, contentType)

frontend/src/features/units/UnitView.tsx
  - Fixed API call to use getUnitContents
  - Fixed delete to include unitId
  - Updated field references (contentType)
```

---

## Success Criteria

**MVP Complete When:**
1. ✅ User can log in
2. ✅ User can create/view a unit
3. ✅ User can create content with AI assistance
4. ✅ User can edit content in WYSIWYG editor
5. ✅ User can save content
6. ✅ User can view saved content in unit
7. ⏳ User can export content (HTML copy, PDF download) - Phase 4

---

## Next Steps

1. **Test the MVP flow** - Run both frontend and backend, verify end-to-end
2. **Phase 3**: Add tiptap-markdown for proper markdown storage
3. **Phase 4**: Add Quarto export functionality
4. **Phase 5-6**: Content types and polish
