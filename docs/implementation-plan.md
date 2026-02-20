# Implementation Plan — Curriculum Curator

> Phased roadmap from current state to usable product.
> Each phase builds on the previous one. Stories reference
> [user-stories.md](user-stories.md).

## Guiding Principles

1. **Manual first, then AI** — if you can't do it by hand, AI-assist will be broken too.
2. **End-to-end over feature breadth** — a complete flow for one path beats half-done everything.
3. **No forced workflow** — users work their way; the system adapts to whatever they provide.
4. **Progressive quality** — minimal input works, more detail = better output.

---

## Phase 1: Solid Manual Editing (current — mostly done)

**Goal:** A user can manually create a unit, add all content, and export it.
This is the foundation everything else builds on.

### What's done
- Unit CRUD with metadata (1.1–1.3)
- ULO management — full CRUD, bulk create, reorder, coverage (2.1–2.7)
- Weekly materials — CRUD, reorder, duplicate, filter, status (3.1–3.7)
- Assessments — CRUD, weights, ULO mapping, reorder (4.1–4.6)
- Rich text editor — TipTap with tables, code blocks (3.2)
- AI content generation — streaming, multi-provider, pedagogy-aware (5.1–5.5, 5.7)
- Analytics — overview, progress, workload, quality scores, validation (7.4–7.7, 8.1–8.5)
- IMSCC export (9.1)
- Auth, admin, settings (10.x, 11.x)
- Citations (12.2–12.3)
- LRD workflow (14.x)

### What needs verification

These are marked "Done" but should be smoke-tested as an end-to-end flow:

| Task | Stories | What to verify |
|------|---------|---------------|
| **Create → Edit → Save roundtrip** | 3.1, 3.2 | Create a material, edit in TipTap, save, reload — does content persist correctly? |
| **ULO → Material → Assessment alignment** | 2.4, 4.3 | Map a ULO to both a material and assessment. Does the coverage report (2.5) reflect it? |
| **IMSCC export** | 9.1 | Export a unit with materials and ULOs. Import the .imscc into Canvas/Blackboard sandbox. |
| **AI generation flow** | 5.1, 5.3 | Generate content with a selected pedagogy. Does the output actually use that style? |
| **Analytics accuracy** | 8.1–8.5 | Do dashboard numbers match reality after adding/removing content? |

**Exit criteria:** One person can create a complete 12-week unit manually, with ULOs, materials, assessments, and export to IMSCC — without hitting bugs.

---

## Phase 2: AI Integration & Smart Completion

**Goal:** AI assists at every level — from scaffolding a whole unit to filling a single field.
This is the killer feature.

### 2A. Context-Aware AI Sidebar (5.8)

**Problem:** The AI assistant sidebar works but doesn't know what unit you're looking at.

**Work:**
- Pass `unitId` from `UnitPage.tsx` → `AIAssistant.tsx`
- Backend: load unit context (title, ULOs, topics, materials, assessments) and include in the LLM prompt
- AI responses become relevant: "Your ULO3 has no assessment mapping — consider adding a quiz in week 8"

**Effort:** Small — wiring change, no new service needed.

### 2B. One-Click Unit Scaffold (1.6, 5.6)

**Problem:** `workflow_structure_creator` can generate a full unit structure, but UX requires going through the multi-stage chat workflow.

**Work:**
- Add a "Quick Scaffold" button on unit creation: enter title → AI generates topics, ULOs, assessments, weekly plan
- Reuse existing `workflow_structure_creator` backend
- Present results for review before saving (don't auto-save)
- User can accept all, accept with edits, or discard

**Effort:** Medium — new UI component, reuse backend.

### 2C. Fill the Gaps (1.7, 5.10, 2.8, 16.3)

**Problem:** User has a partially complete unit. They want the system to identify what's missing and generate it.

**Work:**
- Unit dashboard already shows completeness via analytics. Add actionable buttons:
  - "No ULOs defined" → "Generate ULOs" button
  - "Week 5 has no materials" → "Generate materials for week 5"
  - "Assessment weights total 70%" → "Suggest additional assessment"
- Each button calls existing AI generation with the unit's current state as context
- Batch mode: "Fill all gaps" generates everything missing in one pass
- Individual mode: per-field "Generate" buttons

**Effort:** Medium-large — new UI, new backend endpoint to orchestrate gap-filling.

### 2D. Per-Field AI Assist (5.9)

**Problem:** AI help is only via the sidebar or content generation page. User wants AI on any text field.

**Work:**
- Add a small AI icon/button next to text inputs and textareas throughout the app
- Click → popover with options: "Generate from scratch", "Improve existing", "Get suggestions"
- Uses unit context (like 2A) for relevance
- Start with: material description, ULO text, assessment description

**Effort:** Medium — reusable component, but touches many pages.

### 2E. Simple Version Control (13.1–13.4)

**Problem:** Version history UI components exist but may not work end-to-end.

**Work:**
- Verify the DB-backed version flow: edit material → save → version record created
- Verify diff viewer shows meaningful changes
- Verify restore works (revert to previous version)
- Add explicit "Save as version" / "Commit" button (vs auto-save)
- Keep it simple — no branching, no git. Just: save, view history, restore.

**Effort:** Small-medium — mostly verification and wiring, components exist.

### 2F. Editor Modes (15.1–15.2)

**Problem:** No toggle between simple (rich text) and advanced (YAML + markdown) editing.

**Work:**
- Add a toggle switch on the material editor: "Simple" / "Advanced"
- Simple = TipTap rich editor (current default)
- Advanced = raw markdown textarea + YAML front matter editor (QuartoEditor components exist)
- Persist preference per user

**Effort:** Small — components exist, need a toggle wrapper.

### 2G. Import → Edit Flow (6.1–6.3, 6.7)

**Problem:** Import services work in the backend but the flow from "upload → review → create → edit" isn't connected in the UI.

**Work:**
- Wire import UI: upload file → show extracted structure (topics, ULOs, materials) → user reviews/edits → confirm → creates unit with content
- After import, redirect to normal unit editing page
- Backend already handles PDF/DOCX/PPTX extraction and unit structure creation

**Effort:** Medium — UI integration work, backend ready.

### Phase 2 Priority Order

Do these in order — each builds on the previous:

1. **2E. Version Control** — safety net before changing edit flows
2. **2A. Context-Aware Sidebar** — low effort, high visibility
3. **2F. Editor Modes** — quick win for power users
4. **2G. Import → Edit Flow** — connects existing backend to UI
5. **2B. One-Click Scaffold** — the "wow" feature
6. **2C. Fill the Gaps** — the sticky feature (keeps users coming back)
7. **2D. Per-Field AI Assist** — polish, do last

**Exit criteria:** A user can start with just a title, scaffold a unit, manually adjust parts they care about, have AI fill the rest, and see version history of their changes.

---

## Phase 3: Advanced Import/Export & Research

**Goal:** Full round-trip with LMS platforms and external research.

| Task | Stories | Description |
|------|---------|-------------|
| **Web search for similar courses** | 12.1, 12.4 | Implement `web_search_service` — search for similar units, user selects results, system uses them as context for generation |
| **IMSCC import** | 9.2 | Parse .imscc files → create unit. Spec exists, needs implementation |
| **HTML export for LMS** | 9.3, 9.5 | Export material as standalone HTML with inline styles. "Copy to clipboard" for LMS pasting |
| **Quarto PDF/PPTX export** | 9.4 | Wire `quarto_service` to a UI button. Requires Quarto CLI installed |
| **Image upload** | 15.4 | Media upload endpoint + file storage + TipTap image insert |
| **Image URL insert** | 15.3 | Add "Insert image from URL" to TipTap toolbar |
| **PPTX image extraction** | 6.6 | Extract images from PowerPoint during import, store and reference |
| **AI-enhanced import** | 6.4 | After import, offer "Enhance with AI" that improves imported content |
| **Unit duplication** | 1.5 | Deep-copy a unit for a new semester |

**Exit criteria:** Full round-trip — export unit to Canvas, make changes in Canvas, re-import .imscc, continue editing in Curriculum Curator.

---

## Phase 4: Polish & Advanced Intelligence

**Goal:** Professional-grade quality tools and advanced AI features.

| Task | Stories | Description |
|------|---------|-------------|
| **Content validators** | 7.1–7.3 | Implement readability, structure, and accessibility validators |
| **AI image generation** | 15.5 | Generate diagrams/illustrations via DALL-E or similar |
| **Stock image search** | 15.6 | Unsplash API integration for free images |
| **Standalone content creation** | 16.2 | Create materials without a parent unit for quick one-off needs |

---

## What We're NOT Building (Scope Boundaries)

These are explicitly out of scope to keep focus:

- **Video hosting** — link to YouTube/Vimeo, don't host video files
- **Real-time collaboration** — single-user editing, not Google Docs
- **Git branching/merging** — simple version history only
- **Mobile app** — responsive web is sufficient
- **Student-facing features** — this is a content authoring tool, not an LMS
- **Course (degree program) management** — this manages individual units only

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| DB-backed versioning over Git | Git content service is 70% done but DB versioning is simpler, works now, and meets the "save/view/restore" requirement. Can add git later if needed. |
| Video = links only | Hosting video is a different problem (storage, transcoding, bandwidth). Links to YouTube/Vimeo are sufficient for course materials. |
| No forced workflow | Educators have different preferences. The system should work whether they start with ULOs, with a title, with a PDF import, or with just one material. |
| Web search as Phase 3 | High complexity (needs SearXNG or similar), moderate value. Core editing + AI assist is more important first. |
| Per-field AI assist is last in P2 | Touches many UI components. Get the sidebar context-aware first (one place), then spread to individual fields. |

*Last updated: 2026-02-20*
