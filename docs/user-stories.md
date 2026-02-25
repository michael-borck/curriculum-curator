# User Stories — Curriculum Curator

> Living document tracking what the system does and should do.
> Status: **Done** | **Partial** | **Planned** | **Cut**
>
> Phase tags (P1–P4) indicate implementation priority — see
> [implementation-plan.md](implementation-plan.md) for the phased roadmap.

## Personas

| Alias | Role | Primary Goal |
|-------|------|-------------|
| **Creator** | Lecturer building a new unit from scratch | Generate complete, aligned materials fast |
| **Enhancer** | Educator with existing materials to modernise | Improve legacy content without starting over |
| **Curator** | Department head / quality assurer | Ensure consistency and standards across units |
| **Admin** | System administrator | Manage users, providers, and platform config |

---

## 1. Unit Setup & Structure

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 1.1 | As a **Creator**, I want to create a new unit with metadata (title, code, credits, semester, weeks) so I have a container for all my materials. | P1 | **Done** |
| 1.2 | As a **Creator**, I want to define weekly topics for my unit so content is organised by teaching week. | P1 | **Done** |
| 1.3 | As a **Creator**, I want to set a teaching philosophy (from 9 options) for my unit so AI-generated content matches my pedagogical approach. | P1 | **Done** |
| 1.4 | As an **Enhancer**, I want to import a unit outline (PDF/document) so the system can pre-populate structure from my existing syllabus. | P2 | **Done** — PDF import flow with review UI |
| 1.5 | As a **Creator**, I want to duplicate an existing unit as a starting point for a new semester. | P2 | **Done** — `POST /api/units/{id}/duplicate` |
| 1.6 | As a **Creator**, I want to type just a title/topic and have AI scaffold an entire unit (topics, ULOs, assessments, weekly plan) in one action. | P2 | **Done** — "Quick Scaffold" button on UnitPage |
| 1.7 | As a **Creator**, I want the system to show me what's missing in my unit and offer to fill the gaps (generate missing ULOs, topics, materials, assessments). | P2 | **Done** — `POST /api/ai/fill-gap` endpoint |
| 1.8 | As a **Creator**, I want to choose from structure presets (lecture-heavy, seminar, practical, etc.) when creating a unit so I get a sensible starting layout without manual setup. | P1 | **Done** — preset selector in Create Unit modal |
| 1.9 | As a **Creator**, I want a streamlined Create Unit form that only asks essential fields upfront, with a "Create and Import" shortcut to jump straight into importing materials. | P1 | **Done** — slim form + "Create and Import" button |
| 1.10 | As a **Creator**, I want to customise the time-period label for my unit (Week, Module, Topic, etc.) so the UI matches my institution's terminology. | P1 | **Done** — configurable `topicLabel` on unit |
| 1.11 | As a **Creator**, I want a Settings tab on my unit page where I can edit academic details (year, semester, delivery mode, credit points) and toggle optional features (accreditation mappings, SDGs, AoL, quality/UDL metrics) per unit. | P1 | **Done** — UnitSettings component with feature toggles stored in `unit_metadata.features` |
| 1.12 | As a **Creator**, I want to define custom alignment frameworks (e.g. PLOs, ABET criteria, graduate attributes) with named items, and map my ULOs to them, so I can demonstrate alignment to any accreditation or institutional standard. | P1 | **Done** — `CustomAlignmentFramework` model, presets (PLO, Graduate Attributes, ABET, AQF), CRUD API, mapping UI on UnitPage |

## 2. Learning Outcomes

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 2.1 | As a **Creator**, I want to define Unit Learning Outcomes (ULOs) with Bloom's taxonomy levels so I can track what students should achieve. | P1 | **Done** |
| 2.2 | As a **Creator**, I want to bulk-create ULOs (e.g. paste a list) so I don't have to enter them one by one. | P1 | **Done** |
| 2.3 | As a **Creator**, I want to reorder ULOs by drag-and-drop so they reflect my preferred sequence. | P1 | **Done** |
| 2.4 | As a **Creator**, I want to map ULOs to materials and assessments so I can verify constructive alignment. | P1 | **Done** |
| 2.5 | As a **Creator**, I want to see a coverage report showing which ULOs are covered by materials and assessments (and which have gaps). | P1 | **Done** |
| 2.6 | As a **Curator**, I want to map ULOs to accreditation graduate attributes so I can demonstrate standards compliance. | P1 | **Done** |
| 2.7 | As a **Creator**, I want to define Local Learning Outcomes (LLOs) per material for granular weekly objectives. | P1 | **Done** |
| 2.8 | As a **Creator**, I want AI to suggest ULOs based on my unit title and description so I have a starting point. | P2 | **Done** — included in Quick Scaffold |

## 3. Weekly Materials

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 3.1 | As a **Creator**, I want to add materials (lecture, tutorial, lab, quiz, reading, etc.) to a specific week so my content is organised chronologically. | P1 | **Done** |
| 3.2 | As a **Creator**, I want to edit material content in a rich-text editor (headings, tables, code blocks) so I can produce professional-looking content. | P1 | **Done** — TipTap editor |
| 3.3 | As a **Creator**, I want to reorder materials within a week via drag-and-drop. | P1 | **Done** |
| 3.4 | As a **Creator**, I want to duplicate a material (same week or different week) so I can reuse structure. | P1 | **Done** |
| 3.5 | As a **Creator**, I want to see a week summary (material count, total duration, types breakdown). | P1 | **Done** |
| 3.6 | As a **Creator**, I want to filter materials by type, status, or search term. | P1 | **Done** |
| 3.7 | As a **Creator**, I want to set material status (draft → review → published) to track my progress. | P1 | **Done** |
| 3.8 | As a **Creator**, I want to create just a single quiz, worksheet, or material without needing a full unit structure — no ULOs required, no forced workflow. | P1 | **Done** — materials are independent of ULO mappings |
| 3.9 | As a **Creator**, I want to link to external videos (YouTube, Vimeo) in my materials rather than uploading video files. | P1 | **Done** — content field supports links |
| 3.10 | As a **Creator**, I want to add and delete weeks dynamically so I can adjust my unit's duration without recreating it. | P1 | **Done** — add/delete week buttons on WeekAccordion; delete shifts subsequent weeks down |
| 3.11 | As a **Creator**, I want to assign materials to content categories (Pre-class, In-class, Post-class, Resources) so weekly content is organised by when students engage with it. | P1 | **Done** — `category` field on materials; grouped display in WeekAccordion |
| 3.12 | As a **Creator**, I want to apply Week 1's material structure to all empty weeks in one click, choosing between full material stubs or category-only placeholders, so I don't have to set up each week manually. | P1 | **Done** — "Apply Structure" button with stubs/categories mode selection |

## 4. Assessments

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 4.1 | As a **Creator**, I want to define assessments with type, weight, due week, and duration. | P1 | **Done** |
| 4.2 | As a **Creator**, I want assessment weights to be validated (must total 100%). | P1 | **Done** |
| 4.3 | As a **Creator**, I want to map assessments to ULOs so I can verify alignment. | P1 | **Done** |
| 4.4 | As a **Creator**, I want to duplicate an assessment to create variations. | P1 | **Done** |
| 4.5 | As a **Creator**, I want to reorder assessments. | P1 | **Done** |
| 4.6 | As a **Creator**, I want to link assessments to specific materials (assessment-material links). | P1 | **Done** |
| 4.7 | As a **Creator**, I want to attach a rubric to an assessment, choosing from 4 formats (analytic grid, single-point, holistic, checklist) so marking criteria are clear to students. | P1 | **Done** — RubricEditor with type selector, collapsible disclosure |
| 4.8 | As a **Creator**, I want to define an analytic rubric with editable performance levels (columns) and criteria rows (with weight and per-cell descriptions) so I can spell out expectations at each quality tier. | P1 | **Done** — AnalyticEditor sub-component with add/remove rows & columns |
| 4.9 | As a **Creator**, I want to switch a rubric's type (e.g. analytic → holistic) with a confirmation warning, so I can change my mind without accidentally losing work. | P1 | **Done** — type change triggers confirm dialog if rubric has data |
| 4.10 | As a **Creator**, I want to see at a glance whether an assessment has a rubric (badge on the card) and a summary of its shape (e.g. "Analytic: 4 criteria, 5 levels") without expanding the editor. | P1 | **Done** — purple "Rubric" badge on AssessmentCard, summary text in collapsed disclosure |

## 5. AI-Assisted Content Creation

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 5.1 | As a **Creator**, I want to generate content for a material using AI (selecting provider and teaching style) so I get a quality first draft. | P1 | **Done** — streaming SSE |
| 5.2 | As a **Creator**, I want to enhance existing content with AI (improve readability, add examples, restructure). | P1 | **Done** |
| 5.3 | As a **Creator**, I want AI generation to respect my chosen teaching philosophy. | P1 | **Done** — 9 pedagogies supported |
| 5.4 | As a **Creator**, I want to choose between LLM providers (OpenAI, Anthropic, Gemini, local Ollama). | P1 | **Done** — multi-provider service |
| 5.5 | As a **Creator**, I want a guided content workflow (chat-style) that walks me through creating a unit outline step by step. | P1 | **Done** — `content_workflow_service` |
| 5.6 | As a **Creator**, I want AI to generate the full unit structure (topics, outcomes, assessments) from a unit description. | P2 | **Done** — Quick Scaffold with review UI |
| 5.7 | As a **Creator**, I want to use prompt templates so I can customise how AI generates content. | P1 | **Done** — CRUD for templates |
| 5.8 | As a **Creator**, I want the AI sidebar to be aware of my active unit (its ULOs, topics, materials) so suggestions are contextual, not generic. | P2 | **Done** — AIAssistant receives unitId, unitTitle, unitULOs |
| 5.9 | As a **Creator**, I want AI-assist available on any text field (generate from blank, improve existing, get recommendations) so I don't have to use the sidebar for everything. | P2 | **Done** — AIAssistField component |
| 5.10 | As a **Creator**, I want to partially complete a unit (e.g. some ULOs and a couple of topics) and have AI generate the rest, using what I've provided as context. | P2 | **Done** — fill-gap endpoint |
| 5.11 | As a **Creator**, I want to save an AI assistant response directly as unit content so I don't have to copy-paste between the chat and the editor. | P2 | **Done** — SaveToUnitButton on assistant messages with content type selector and unit picker modal |

## 6. Content Import & Enhancement

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 6.1 | As an **Enhancer**, I want to upload existing materials (PDF, DOCX, PPTX, MD, HTML) so the system can parse and import them. | P2 | **Done** — ImportMaterials + PDFImportDialog |
| 6.2 | As an **Enhancer**, I want the system to extract structure from uploaded PDFs (topics, outcomes, assessments). | P2 | **Done** — `pdf_parser_service` + `document_analyzer_service` |
| 6.3 | As an **Enhancer**, I want to review and correct auto-detected structure before committing the import. | P2 | **Done** — review UI with week assignment |
| 6.4 | As an **Enhancer**, I want AI to enhance imported content while preserving my original intent. | P3 | **Done** — "Enhance with AI" button after import, batch enhance all materials |
| 6.5 | As an **Enhancer**, I want batch import of multiple files at once (or ZIP upload). | P2 | **Done** — ZIP analysis and import |
| 6.6 | As an **Enhancer**, I want to import a PowerPoint and have it converted to editable content (text extracted, slides become sections). | P3 | **Done** — text + image extraction via `python-pptx`, images stored in content repo |
| 6.7 | As an **Enhancer**, I want imported content to go straight into the normal editing flow so I can refine it immediately. | P2 | **Done** — import flow redirects to editing |
| 6.8 | As an **Enhancer**, I want to extract the theme (colours, fonts, layouts) from an imported PPTX and save it as an export template, so future PPTX exports use my existing branding. | P2 | **Done** — opt-in checkbox on Import Materials; strips content slides, keeps masters/layouts/theme (ADR-056) |

## 7. Content Validation & Quality

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 7.1 | As a **Curator**, I want automatic readability scoring (Flesch-Kincaid) on generated content. | P3 | **Done** — 9 plugins wired with API endpoints + editor quality panel |
| 7.2 | As a **Curator**, I want structure validation (heading hierarchy, section balance). | P3 | **Done** — grammar, spell-check, structure validators with Australian English support |
| 7.3 | As a **Curator**, I want accessibility checking (WCAG compliance). | P4 | **Done** — `accessibility_validator` plugin handles markdown + HTML: alt text, heading structure, link text, tables, color refs, language complexity, video captions, YouTube titles, Mermaid diagrams |
| 7.4 | As a **Curator**, I want an alignment report showing ULO coverage across materials and assessments. | P1 | **Done** — `analytics_service.get_alignment_report` |
| 7.5 | As a **Curator**, I want a quality score for each unit (graded A–F) based on coverage, weights, workload balance. | P1 | **Done** — `analytics_service.calculate_quality_score` |
| 7.6 | As a **Curator**, I want unit validation that flags errors (missing ULOs, weights != 100%, no materials). | P1 | **Done** — `analytics_service.validate_unit` |
| 7.7 | As a **Curator**, I want recommendations for improving a unit (AI-generated suggestions). | P1 | **Done** — `analytics_service.get_recommendations` |
| 7.8 | As a **Curator**, I want automatic markdown cleanup (fix copy-paste artefacts, heading hierarchy, list formatting, code block detection) so pasted or LLM-generated content is well-structured. | P3 | **Done** — `markdown_cleanup` remediator plugin, available via Auto-fix All |
| 7.9 | As a **Curator**, I want a UDL (Universal Design for Learning) inclusivity score that measures representation diversity, engagement variety, action & expression options, and content accessibility — per-week and per-unit — so I can identify which weeks need more inclusive design. | P2 | **Done** — `udl_service` with Shannon entropy scoring, 4 dimensions, star ratings, rule-based suggestions (ADR-057) |
| 7.10 | As a **Curator**, I want to toggle visibility of individual quality and UDL metric dimensions in Unit Settings, so I only see the metrics relevant to my context. | P1 | **Done** — `QualityMetricVisibility` and `UDLMetricVisibility` in `unit_metadata.features`; toggles in UnitSettings |

## 8. Analytics & Reporting

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 8.1 | As a **Creator**, I want a unit overview dashboard (counts of ULOs, materials, assessments, total weight). | P1 | **Done** |
| 8.2 | As a **Creator**, I want to see unit progress (draft vs published, completion percentage). | P1 | **Done** |
| 8.3 | As a **Creator**, I want weekly workload analysis (duration per week, assessment load). | P1 | **Done** |
| 8.4 | As a **Creator**, I want to export unit data as JSON or CSV for external reporting. | P1 | **Done** |
| 8.5 | As a **Creator**, I want unit statistics (Bloom's distribution, type breakdowns). | P1 | **Done** |

## 9. Export & LMS Integration

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 9.1 | As a **Creator**, I want to export my unit as an IMS Common Cartridge (.imscc) file so I can import it into my LMS (Moodle, Canvas, Blackboard). | P1 | **Done** — IMSCC v1.1 |
| 9.2 | As a **Creator**, I want to import an .imscc file from my LMS to create a unit in the system. | P3 | **Done** — round-trip + generic LMS packages |
| 9.3 | As a **Creator**, I want to export content as standalone HTML (with inline styles) for pasting into an LMS. | P3 | **Done** |
| 9.4 | As a **Creator**, I want to export my unit as PDF, DOCX, or PPTX. | P2 | **Done** — Pandoc + Typst (ADR-033) |
| 9.5 | As a **Creator**, I want to copy formatted content to clipboard for quick LMS pasting. | P3 | **Done** |
| 9.6 | As a **Creator**, I want to export my unit as a SCORM 1.2 package for LMS platforms that don't support Common Cartridge. | P2 | **Done** — ADR-034 |
| 9.7 | As a **Creator**, I want to import a SCORM package from my LMS to create a unit in the system. | P3 | **Done** |
| 9.8 | As a **Creator**, I want to import QTI quiz data from IMSCC/SCORM packages so auto-graded quizzes transfer into the system as structured `QuizQuestion` rows (question text, options, correct answers, points, feedback). | P4 | **Done** — `QTIImporter` auto-detects QTI 1.2/2.1, creates Content + QuizQuestion rows on package import |
| 9.9 | As a **Creator**, I want a mapping table between LMS terminology (Canvas Modules, Moodle Sections, Blackboard Content Areas) and our internal naming (Weeks, Materials, Assessments) so imports are correctly classified. | P4 | **Done** — `lms_terminology.py` with 5 LMS platforms; keyword sets used by package import classifier |
| 9.10 | As a **Creator**, I want to select a target LMS when exporting so the package uses the correct naming conventions and structure for that LMS. | P4 | **Done** — `target_lms` query param on IMSCC/SCORM export routes; LMS dropdown in export menu |
| 9.11 | As a **Creator**, I want to export quizzes as QTI 2.1 XML (standalone ZIP) so I can import them into any LMS quiz bank without exporting the full unit. | P4 | **Done** — `GET /api/units/{id}/export/qti` returns QTI 2.1 package ZIP |
| 9.12 | As a **Creator**, I want IMSCC/SCORM exports to embed QTI quiz items so quizzes import as interactive, auto-graded assessments in the LMS — not just static description pages. | P4 | **Done** — QTI 1.2 XML embedded in IMSCC (CC assessment resource type) and SCORM exports |

## 10. Authentication & User Management

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 10.1 | As a **user**, I want to register with email/password. | P1 | **Done** |
| 10.2 | As a **user**, I want to log in and receive a JWT session. | P1 | **Done** |
| 10.3 | As a **user**, I want to verify my email address. | P1 | **Done** |
| 10.4 | As a **user**, I want to reset my password via email. | P1 | **Done** |
| 10.5 | As a **user**, I want to configure my preferred teaching style in settings. | P1 | **Done** |
| 10.6 | As a **user**, I want to configure my own LLM API keys (bring your own key). | P1 | **Done** |
| 10.7 | As a **user**, I want to set up local Ollama as my AI provider (no cloud keys needed). | P1 | **Done** |

## 11. Administration

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 11.1 | As an **Admin**, I want to manage users (view, roles, deactivate). | P1 | **Done** |
| 11.2 | As an **Admin**, I want to configure system-wide LLM provider settings and API keys. | P1 | **Done** |
| 11.3 | As an **Admin**, I want to manage the email whitelist (allowed registration domains). | P1 | **Done** |
| 11.4 | As an **Admin**, I want to view security logs (login attempts, admin actions). | P1 | **Done** |
| 11.5 | As an **Admin**, I want to configure password policy (min length, complexity). | P1 | **Done** |
| 11.6 | As an **Admin**, I want to configure session and lockout settings. | P1 | **Done** |
| 11.7 | As an **Admin**, I want to view system health and monitoring info. | P1 | **Done** |

## 12. Research & Citation

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 12.1 | As a **Creator**, I want to search the web for academic sources to reference in my materials. | P2 | **Done** — SearXNG integration with academic domain prioritisation |
| 12.2 | As a **Creator**, I want to save research sources with metadata (authors, year, DOI, URL). | P1 | **Done** |
| 12.3 | As a **Creator**, I want to generate citations in multiple formats (APA7, Harvard, MLA, Chicago, IEEE, Vancouver). | P1 | **Done** |
| 12.4 | As a **Creator**, I want to search for similar courses/units across the internet, see results with titles and descriptions, select the ones I like, and use those as a basis for my unit structure. | P3 | **Done** — Research page with tiered academic search, URL extraction, scaffold/compare/reading-list actions (ADR-039) |

## 13. Version Control & History

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 13.1 | As a **Creator**, I want to save a version of my material when I'm happy with it ("commit"). | P2 | **Done** — Git-backed per-unit repositories |
| 13.2 | As a **Creator**, I want to see previous versions of a material and compare changes (diff view). | P2 | **Done** — VersionHistory + diff viewer |
| 13.3 | As a **Creator**, I want to restore a previous version if I don't like my changes. | P2 | **Done** — restore via Git |
| 13.4 | As a **Creator**, I want simple version control — just save/view/restore, no branches or merging. | P2 | **Done** — Git used as storage, no branching exposed |

## 14. LRD Workflow (Learning Requirements Document)

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 14.1 | As a **Creator**, I want to create a structured Learning Requirements Document for comprehensive unit planning. | P1 | **Done** |
| 14.2 | As a **Creator**, I want to submit an LRD for approval before generating content. | P1 | **Done** |
| 14.3 | As a **Creator**, I want to generate a prioritised task list from an approved LRD. | P1 | **Done** |
| 14.4 | As a **Creator**, I want to track task completion as I work through LRD-generated tasks. | P1 | **Done** |

## 15. Editor Experience

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 15.1 | As a **Creator**, I want a simple editing mode that hides technical details (YAML, raw markdown) so I can focus on content. | P2 | **Done** — EditorModeToggle component |
| 15.2 | As a **power user**, I want an advanced editing mode where I can see and edit YAML front matter and raw markdown directly. | P2 | **Done** — toggle between simple/advanced |
| 15.3 | As a **Creator**, I want to add images to my materials by providing a URL/link. | P3 | **Done** — TipTap image extension with URL insert dialog |
| 15.4 | As a **Creator**, I want to upload images from my computer to include in materials. | P3 | **Done** — image upload endpoint + TipTap toolbar button with preview |
| 15.5 | ~~As a **Creator**, I want AI to generate images for my materials.~~ | P4 | **Cut** — outside core scope; educators have dedicated image tools |
| 15.6 | ~~As a **Creator**, I want to search for free stock images (e.g. Unsplash) and insert them.~~ | P4 | **Cut** — adds API dependency for marginal value; use browser instead |
| 15.9 | As a **Creator**, I want to generate an image prompt from my material content (with style options like realistic, sketch, diagram) so I can copy it into my preferred image tool. | P3 | **Done** — editor toolbar wand button opens slide-out panel; pick style + aspect ratio → LLM generates copy-paste prompt |
| 15.7 | As a **Creator**, I want to embed Mermaid diagrams (flowcharts, sequence diagrams) in my materials so I can visualise concepts. | P2 | **Done** — TipTap Mermaid node with live preview |
| 15.8 | As a **Creator**, I want to embed YouTube/video links as rich previews in my materials. | P2 | **Done** — TipTap Video/YouTube nodes |

## 16. Desktop App & Distribution

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 16.1 | As a **user**, I want to download and run Curriculum Curator as a desktop app (macOS, Windows, Linux) without needing Docker or command-line tools. | P3 | **Done** — Electron app with embedded PyInstaller backend (ADR-035) |
| 16.2 | As a **user**, I want the desktop app to work with a locally installed Ollama for AI, so I don't need cloud API keys. | P3 | **Done** — Ollama detection, auto-start, and graceful shutdown |
| 16.3 | As a **user**, I want PDF/PPTX export in the desktop app, even if I need to install Pandoc separately and point the app to it. | P3 | **Done** — Pandoc + Typst bundled in app resources |
| 16.4 | As a **user**, I want the desktop app to auto-update so I don't have to re-download each release. | P3 | **Done** — electron-updater with GitHub Releases |

## 17. Flexibility & Workflow Freedom

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 17.1 | As a **Creator**, I want to work on my unit in any order — I shouldn't be forced to define ULOs before creating materials, or complete all weeks before exporting. | P1 | **Done** — no enforced sequence |
| 17.2 | As a **Creator**, I want to create a standalone piece of content (a quiz, a worksheet) without setting up a full unit, for quick one-off needs. | P3 | **Done** — Quick Create modal on dashboard; auto-generates lightweight unit behind the scenes |
| 17.3 | As a **Creator**, I want quality to improve progressively — the system should work with minimal input but produce better results as I add more detail (ULOs, descriptions, pedagogy). | P2 | **Done** — fill-gap + scaffold respect existing context |

---

## Status Summary

| Status | Count |
|--------|-------|
| **Done** | ~115 |
| **Cut** | 2 |

| Phase | Description | Status |
|-------|-------------|--------|
| **P1** | Manual editing, core CRUD, auth, analytics, IMSCC export | **Complete** |
| **P2** | AI integration, smart completion, import flow, version control, editor UX, SCORM/document export | **Complete** |
| **P3** | Desktop app, IMSCC/SCORM import, image handling, research, plugin system | **Complete** |
| **P4** | Accessibility validation, LMS terminology mapping, LMS-targeted export | **Complete** |

### Cut Stories

| # | Story | Reason |
|---|-------|--------|
| 15.5 | AI image generation | Outside core scope — educators have dedicated tools; upload path (15.4) covers the need |
| 15.6 | Unsplash stock image search | Marginal value vs API/licensing complexity; any browser can search Unsplash |

*Last updated: 2026-02-25*
