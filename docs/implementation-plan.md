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

## Phase 1: Solid Manual Editing — COMPLETE

**Goal:** A user can manually create a unit, add all content, and export it.

**Status:** All ~50 stories done. Verified with end-to-end API smoke tests (24 tests) and service-level unit tests.

### What was delivered
- Unit CRUD with metadata (1.1–1.3)
- ULO management — full CRUD, bulk create, reorder, coverage (2.1–2.7)
- Weekly materials — CRUD, reorder, duplicate, filter, status (3.1–3.9)
- Assessments — CRUD, weights, ULO mapping, reorder (4.1–4.6)
- Rich text editor — TipTap with tables, code blocks (3.2)
- AI content generation — streaming, multi-provider, pedagogy-aware (5.1–5.5, 5.7)
- Analytics — overview, progress, workload, quality scores, validation (7.4–7.7, 8.1–8.5)
- IMSCC v1.1 export (9.1)
- Auth, admin, settings (10.x, 11.x)
- Citations (12.2–12.3)
- LRD workflow (14.x)
- Flexible workflow — no enforced sequence (17.1)

---

## Phase 2: AI Integration & Smart Completion — COMPLETE

**Goal:** AI assists at every level — from scaffolding a whole unit to filling a single field.

**Status:** All major stories done including several originally planned for P3.

### What was delivered

| Feature | Stories | Implementation |
|---------|---------|---------------|
| **Context-Aware AI Sidebar** | 5.8 | AIAssistant receives unitId, unitTitle, unitULOs — responses are contextual |
| **One-Click Unit Scaffold** | 1.6, 5.6 | "Quick Scaffold" button → AI generates ULOs, topics, assessments → review modal → accept/edit/discard |
| **Fill the Gaps** | 1.7, 5.10, 2.8 | `POST /api/ai/fill-gap` — generates missing ULOs, materials, or assessments using unit context |
| **Per-Field AI Assist** | 5.9 | AIAssistField component — inline Sparkles button on text fields (generate, improve, suggest) |
| **AI Assistance Levels** | ADR-0032 | Three levels (none/refine/create) — lecturer controls AI involvement |
| **Version Control** | 13.1–13.4 | Git-backed per-unit repositories — save, view history, diff, restore |
| **Editor Modes** | 15.1–15.2 | EditorModeToggle — simple (TipTap) / advanced (YAML + markdown) |
| **Import → Edit Flow** | 6.1–6.3, 6.5, 6.7 | Upload → analysis → review structure → assign to weeks → create unit |
| **Unit Duplication** | 1.5 | `POST /api/units/{id}/duplicate` — deep copy all relationships |
| **Soft Delete / Archive** | ADR-0031 | Archive with full restore, two-step delete modal in UI |
| **Web Search** | 12.1 | SearXNG integration with academic domain prioritisation |
| **SCORM 1.2 Export** | 9.6 | ADR-0034 — universal LMS compatibility alongside IMSCC v1.1 |
| **Document Export** | 9.4 | ADR-0033 — Pandoc + Typst pipeline for PDF, DOCX, PPTX, HTML |
| **Progressive Quality** | 17.3 | Scaffold + fill-gap respect existing context |

---

## Phase 3: Desktop App, Images & Advanced Import/Export — IN PROGRESS

**Goal:** Downloadable app, image support, and full round-trip with LMS platforms.

### 3A. Desktop App — Electron Wrapper (16.1–16.4)

**What already exists:**
- `LOCAL_MODE` — auto-login, no JWT, privacy-first (working)
- PyInstaller compatibility audit — ADR-0024, all dependency blockers identified
- Ollama sidecar architecture — ADR-0025
- Pandoc + Typst export service — ADR-0033 (working in Docker)
- Electron scaffolding started in `desktop/` directory

**What was delivered:**
- `desktop/src/main/` — backend lifecycle, Ollama auto-start, IPC bridge
- Electron-builder config for macOS/Windows/Linux
- GitHub Actions workflow for cross-platform builds
- Auto-update via electron-updater
- Ollama detection, auto-start, graceful shutdown
- Platform-aware install guidance + local AI quality notices

**What remains:**
- PyInstaller bundling of the backend for production builds
- Bundle Pandoc + Typst binaries as `extraResources` (~60MB total — this is why we chose them over Quarto's ~500MB+)

**Resolved decisions:**

| Decision | Outcome |
|----------|---------|
| **PDF/PPTX export** | Pandoc + Typst bundled as `extraResources` in Electron. Docker also bundles both. Path detection already wired in `backend.ts`. |
| **Ollama** | Detect on startup, auto-start if installed, guide user to download if missing. Done. |
| **Backend bundling** | PyInstaller single-file executable (ADR-0024 audit done). Not yet implemented. |

### 3B. LMS Import/Export Roundtrip

| Task | Stories | Description |
|------|---------|-------------|
| **IMSCC import** | 9.2 | Parse .imscc files → create unit. Spec exists, needs implementation |
| **HTML export for LMS** | 9.3, 9.5 | Export material as standalone HTML with inline styles. "Copy to clipboard" for LMS pasting |

### 3C. Image Support

| Task | Stories | Description |
|------|---------|-------------|
| **Image URL insert** | 15.3 | Add "Insert image from URL" to TipTap toolbar |
| **Image upload** | 15.4 | Media upload endpoint + file storage + TipTap image insert |
| **PPTX image extraction** | 6.6 | Extract images from PowerPoint during import, store and reference |

### 3D. Remaining Items

| Task | Stories | Description |
|------|---------|-------------|
| **Similar course search** | 12.4 | Search for similar units across the web, use as context for generation |
| **AI-enhanced import** | 6.4 | After import, offer "Enhance with AI" to improve imported content |
| **Standalone content creation** | 17.2 | Create materials without a parent unit for quick one-off needs |
| **Content validators** | 7.1–7.2 | Implement readability scoring and structure validation plugins |

**Exit criteria:** Download `.dmg` or `.exe`, launch app, create a unit, generate AI content (with API key or local Ollama), export to IMSCC/SCORM. Image insertion works via URL.

---

## Phase 4: Polish & Advanced Intelligence

**Goal:** Professional-grade quality tools and advanced AI features.

| Task | Stories | Description |
|------|---------|-------------|
| **Accessibility checking** | 7.3 | WCAG compliance validation |
| **AI image generation** | 15.5 | Generate diagrams/illustrations via DALL-E or similar |
| **Stock image search** | 15.6 | Unsplash API integration for free images |

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
| Git-backed versioning | Per-unit Git repos provide content history, diffing, and restore without exposing Git complexity to users. |
| Video = links only | Hosting video is a different problem (storage, transcoding, bandwidth). Links to YouTube/Vimeo are sufficient. |
| No forced workflow | Educators have different preferences. The system works whether they start with ULOs, a title, a PDF, or one material. |
| IMSCC v1.1 (not 1.2) | Moodle only supports CC 1.0–1.1. Our webcontent-only exports are identical across versions. v1.1 maximises LMS compatibility. |
| SCORM 1.2 (not 2004) | SCORM 1.2 is universally supported. 2004 adds sequencing complexity we don't need for content delivery. |
| Pandoc + Typst (not Quarto) | ADR-0033. Pandoc + Typst = ~60MB vs Quarto's ~500MB+. No LaTeX needed. Easier to bundle in Docker and desktop app. |
| Electron + external tools for desktop | Accept "install these tools" friction for Pandoc/Typst/Ollama in exchange for shipping sooner. Docker remains the zero-friction option. |
| AI assistance levels | ADR-0032. Lecturers choose their comfort level: none, refine only, or full creation. Respects educator autonomy. |

*Last updated: 2026-02-21*
